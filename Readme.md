Python version 3.12.3

Install dependencies: pip3 install -r requirements.txt

Run: py app.py

---

1. Entrar a la ruta /posts y cambiar el query param role por 'admin', lo cual habilita un campo filtro
2. Inyectar sql en este campo filtro. 'UNION SELECT id as id, username as title, email as content FROM users '
3. ... (apoderarse de la cuenta admin)
4. Logeado como admin, crear un post con contenido malicioso. Ejemplo de contenido: <script>alert('alerta xss')</script>
