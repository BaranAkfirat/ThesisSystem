from flask import Flask, render_template, request
import pyodbc

app = Flask(__name__)

# Veritabanı bağlantı ayarları
DB_SERVER = '******'  
DB_NAME = '*******'  

# Veritabanı bağlantısını oluştur
def get_db_connection():
    try:
        connection = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
        return connection
    except Exception as e:
        print(f"Veritabanı bağlantı hatası: {e}")
        return None

# Ana route
@app.route('/')
def index():
    connection = get_db_connection()
    if connection is None:
        return "Veritabanı bağlantısı kurulamadı", 500

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                t.ThesisID, 
                t.Title, 
                a.AuthorName 
            FROM dbo.Thesis t
            LEFT JOIN dbo.Author a ON t.AuthorID = a.AuthorID
        """)
        rows = cursor.fetchall()

        theses = [{"id": row[0], "title": row[1], "author": row[2]} for row in rows]

        return render_template('index.html', theses=theses)
    except Exception as e:
        return f"Bir hata oluştu: {e}", 500
    finally:
        connection.close()

@app.route('/thesis/<int:thesis_id>')
def thesis_detail(thesis_id):
    connection = get_db_connection()
    if connection is None:
        return "Veritabanı bağlantısı kurulamadı", 500

    try:
        cursor = connection.cursor()
        # Tez detaylarını almak için sorgu
        cursor.execute("""
            SELECT 
                t.Title, 
                t.Abstract, 
                t.Year, 
                t.NumberOfPages, 
                t.SubmissionDate, 
                a.AuthorName, 
                i.InstituteName, 
                l.LanguageName, 
                u.UniversityName
            FROM dbo.Thesis t
            LEFT JOIN dbo.Author a ON t.AuthorID = a.AuthorID
            LEFT JOIN dbo.Institute i ON t.InstituteID = i.InstituteID
            LEFT JOIN dbo.Language l ON t.LanguageID = l.LanguageID
            LEFT JOIN dbo.University u ON i.UniversityID = u.UniversityID
            WHERE t.ThesisID = ?
        """, (thesis_id,))
        thesis = cursor.fetchone()

        if not thesis:
            return "Tez bulunamadı", 404

        # Tez detaylarını bir sözlük olarak hazırlayın
        thesis_details = {
            "title": thesis[0],
            "abstract": thesis[1],
            "year": thesis[2],
            "number_of_pages": thesis[3],
            "submission_date": thesis[4],
            "author": thesis[5],
            "institute": thesis[6],
            "language": thesis[7],
            "university": thesis[8],
        }

        # İlgili anahtar kelimeleri almak için sorgu
        cursor.execute("""
            SELECT k.KeywordText 
            FROM dbo.ThesisKeyword tk
            LEFT JOIN dbo.Keyword k ON tk.KeywordID = k.KeywordID
            WHERE tk.ThesisID = ?
        """, (thesis_id,))
        keywords = [row[0] for row in cursor.fetchall()]
        thesis_details["keywords"] = keywords

        # Danışman bilgilerini almak için sorgu
        cursor.execute("""
            SELECT 
                s.SupervisorName, 
                ts.Role 
            FROM dbo.ThesisSupervisor ts
            LEFT JOIN dbo.Supervisor s ON ts.SupervisorID = s.SupervisorID
            WHERE ts.ThesisID = ?
        """, (thesis_id,))
        supervisors = [{"name": row[0], "role": row[1]} for row in cursor.fetchall()]
        thesis_details["supervisors"] = supervisors

        return render_template('thesis_detail.html', thesis=thesis_details)
    except Exception as e:
        return f"Bir hata oluştu: {e}", 500
    finally:
        connection.close()

@app.route('/search', methods=['GET', 'POST'])
def search_theses():  # Fonksiyon adı değiştirildi
    connection = get_db_connection()
    if connection is None:
        return "Veritabanı bağlantısı kurulamadı", 500

    search_query = ""
    if request.method == 'POST':
        search_query = request.form.get('search', '').strip()

    try:
        cursor = connection.cursor()
        # Tez başlığı ve yazar bilgilerini almak için sorgu
        query = """
            SELECT 
                t.ThesisID, 
                t.Title, 
                a.AuthorName 
            FROM dbo.Thesis t
            LEFT JOIN dbo.Author a ON t.AuthorID = a.AuthorID
        """
        if search_query:
            query += " WHERE t.Title LIKE ?"
            cursor.execute(query, f"%{search_query}%")
        else:
            cursor.execute(query)

        rows = cursor.fetchall()

        # Tez listesini oluştur
        theses = [{"id": row[0], "title": row[1], "author": row[2]} for row in rows]

        return render_template('index.html', theses=theses, search_query=search_query)
    except Exception as e:
        return f"Bir hata oluştu: {e}", 500
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(debug=True)
