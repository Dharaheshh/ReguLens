import psycopg

dburl = "postgresql://postgres:devpass@localhost:5433/regulens"
conn = psycopg.connect(dburl)
cur = conn.cursor()

# Check tables
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
print('TABLES:', [r[0] for r in cur.fetchall()])

# Check extension
cur.execute("SELECT extname FROM pg_extension;")
print('EXTENSIONS:', [r[0] for r in cur.fetchall()])

# Check dimension
cur.execute("""
SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS data_type
FROM pg_attribute a
JOIN pg_class c ON a.attrelid = c.oid
WHERE c.relname = 'chunks' AND a.attname = 'embedding';
""")
print('EMBEDDING_DEF:', cur.fetchone())

# Check indices
cur.execute("SELECT indexname FROM pg_indexes WHERE schemaname = 'public';")
print('INDICES:', [r[0] for r in cur.fetchall()])

cur.execute("SELECT * FROM alembic_version;")
print('ALEMBIC_VERSION:', cur.fetchone())
