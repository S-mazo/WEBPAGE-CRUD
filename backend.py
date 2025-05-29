from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = '1234567890'

DATABASE = os.path.join(os.path.dirname(__file__), 'productos.db')

def init_db():
    with app.app_context():
        db = sqlite3.connect(DATABASE)
        db.execute('''CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            descripcion TEXT)''')
        db.commit()

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

# --- Rutas para el manejo del Loading ---
@app.route('/github_redirect_handler', methods=['POST'])
def github_redirect_handler():
    github_link = request.form.get('github_link')
    if github_link:
        session['github_link'] = github_link
        # Flask redirige a la página de carga
        return redirect(url_for('loading_page'))
    # Si no hay enlace, redirige a la página principal
    return redirect(url_for('home')) 

@app.route('/loading')
def loading_page():
    return render_template('loading.html')

@app.route('/get_github_link')
def get_github_link():
    # Recupera el enlace de GitHub de la sesión y lo elimina para limpiar
    github_link = session.pop('github_link', None) 
    return jsonify({'github_link': github_link})

# --- Rutas existentes de Productos (mantener igual) ---
@app.route('/productos', methods=['GET', 'POST'])
def productos():
    db = get_db()
    if request.method == 'POST':
        data = request.get_json()
        try:
            db.execute('INSERT INTO productos (nombre, precio, descripcion) VALUES (?, ?, ?)',
                       [data['nombre'], data['precio'], data['descripcion']])
            db.commit()
            return jsonify({"mensaje": "Producto guardado correctamente"}), 201 
        except sqlite3.Error as e:
            db.rollback()
            return jsonify({"error": f"Error al guardar el producto: {e}"}), 500
    
    cursor = db.execute('SELECT * FROM productos')
    productos = [dict(row) for row in cursor.fetchall()] 
    return jsonify(productos)

@app.route('/productos/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def producto_id(id):
    db = get_db()
    if request.method == 'GET':
        cursor = db.execute('SELECT * FROM productos WHERE id = ?', [id])
        row = cursor.fetchone()
        if row:
            return jsonify(dict(row)) 
        else:
            return jsonify({"error": "Producto no encontrado"}), 404

    elif request.method == 'PUT':
        data = request.get_json()
        try:
            db.execute('UPDATE productos SET nombre = ?, precio = ?, descripcion = ? WHERE id = ?',
                       [data['nombre'], data['precio'], data['descripcion'], id])
            db.commit()
            return jsonify({"mensaje": "Producto actualizado"})
        except sqlite3.Error as e:
            db.rollback()
            return jsonify({"error": f"Error al actualizar el producto: {e}"}), 500

    elif request.method == 'DELETE':
        try:
            db.execute('DELETE FROM productos WHERE id = ?', [id])
            db.commit()
            return jsonify({"mensaje": "Producto eliminado"})
        except sqlite3.Error as e:
            db.rollback()
            return jsonify({"error": f"Error al eliminar el producto: {e}"}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)