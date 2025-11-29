# PostgreSQL Database Setup

## ✅ Configuration Complete

Your application has been successfully configured to use PostgreSQL (Neon database) instead of SQLite3.

### What Was Done:

1. **Updated `.env` file** with your PostgreSQL connection string:
   ```
   DATABASE_URL=postgresql://neondb_owner:npg_0dIfEsxV5pgR@ep-super-bonus-ahkemh7n-pooler.c-3.us-east-1.aws.neon.tech/wakeupcalls?sslmode=require&channel_binding=require
   ```

2. **Installed PostgreSQL driver** (`psycopg2-binary`)

3. **Ran all migrations** - All database tables have been created in PostgreSQL

### Database Schema Status:

✅ All migrations applied successfully:
- Django core tables (auth, sessions, contenttypes, admin)
- Custom apps (accounts, wakeup_calls, notifications, weather)
- Celery tables (django_celery_beat, django_celery_results)

## 📋 Next Steps

### 1. Create Superuser (Admin Account)

If you need admin access, create a superuser:

```bash
python manage.py createsuperuser
```

### 2. Migrate Existing Data (Optional)

**Important:** If you had data in SQLite that you want to keep:

1. **Export from SQLite:**
   ```bash
   python manage.py dumpdata --exclude auth.permission --exclude contenttypes > backup.json
   ```

2. **Switch to PostgreSQL** (already done ✅)

3. **Import to PostgreSQL:**
   ```bash
   python manage.py loaddata backup.json
   ```

**Note:** If you're starting fresh (no data to migrate), you can skip this step.

### 3. Verify Connection

Test that everything is working:

```bash
python manage.py check
python manage.py shell
>>> from django.db import connection
>>> connection.ensure_connection()
>>> print("✅ Database connection successful!")
```

### 4. Run the Server

Start your development server:

```bash
python manage.py runserver
```

## 🔧 Database Configuration

The database configuration is in `wakeupcalls_project/settings.py`:

```python
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default=f'sqlite:///{BASE_DIR}/db.sqlite3')
    )
}
```

This automatically reads the `DATABASE_URL` from your `.env` file.

## 🔐 Security Notes

- Your `.env` file contains sensitive credentials - **never commit it to git**
- The connection uses SSL (`sslmode=require`) for secure connections
- Consider rotating passwords periodically

## 🐛 Troubleshooting

### Connection Issues

If you see connection errors:

1. **Check the connection string format** - Make sure it's correct in `.env`
2. **Verify network access** - Ensure your IP is allowed in Neon dashboard
3. **Test SSL connection** - The connection requires SSL

### Migration Issues

If migrations fail:

```bash
# Check migration status
python manage.py showmigrations

# Reset migrations (WARNING: Deletes all data)
python manage.py migrate --run-syncdb
```

## 📚 Resources

- [Neon Documentation](https://neon.tech/docs)
- [Django PostgreSQL Setup](https://docs.djangoproject.com/en/4.2/ref/databases/#postgresql-notes)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)

---

**Status:** ✅ PostgreSQL is now your active database!
