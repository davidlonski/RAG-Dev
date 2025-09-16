# Supabase Migration Guide

## Overview

This guide explains how to migrate from direct PostgreSQL connections to Supabase API integration in the RAG-Dev project.

## What Changed

### Before (PostgreSQL Direct Connection)
- Direct database connections using `psycopg2`
- Manual connection management and pooling
- Direct SQL queries with parameterized statements
- Manual transaction management

### After (Supabase API)
- Supabase API client using `supabase-py` library
- Managed connections and automatic pooling
- RESTful API calls with automatic serialization
- Built-in transaction support

## Migration Steps

### 1. Install Supabase Client

```bash
pip install supabase==2.11.1
```

### 2. Update Environment Variables

Add these variables to your `.env` file:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Legacy PostgreSQL Configuration (can be removed)
# POSTGRES_HOST=your-postgres-host
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=your-password
# POSTGRES_PORT=5432
# POSTGRES_DB=postgres
```

### 3. Get Supabase Credentials

1. **Create a Supabase Project**:
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Note your project URL

2. **Get Service Role Key**:
   - Go to Project Settings → API
   - Copy the `service_role` key (not the `anon` key)
   - This key has full database access

### 4. Set Up Database Schema

Run the SQL schema from `app/database/homework_schema_psql.sql` in your Supabase SQL editor:

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy and paste the contents of `homework_schema_psql.sql`
4. Execute the SQL to create all tables

### 5. Test the Migration

Run the test script to verify everything works:

```bash
cd app/database
python test_supabase.py
```

Expected output:
```
🧪 Testing Supabase Database Manager...
✅ Successfully connected to Supabase!
📊 Testing basic operations...
✅ User listing works: Found X users
✅ Assignment listing works: Found X assignments
✅ Basic database operations are working!
🎉 Supabase Database Manager test completed successfully!
```

## Code Changes

### Import Changes

All files now import from the new Supabase database manager:

```python
# Before
from database.db_psql import UserServer, HomeworkServer, ImageServer

# After
from database.db_supabase import UserServer, HomeworkServer, ImageServer
```

### No Application Code Changes Required

The new `DatabaseManagerSupabase` class maintains the exact same interface as the PostgreSQL version, so no changes are needed in your application logic.

## Benefits of Supabase Integration

### 1. **Managed Infrastructure**
- Automatic backups and point-in-time recovery
- Built-in monitoring and alerting
- Automatic scaling and performance optimization

### 2. **Enhanced Security**
- Row Level Security (RLS) policies
- Encrypted connections
- Secure API endpoints

### 3. **Developer Experience**
- Web-based database dashboard
- Auto-generated API documentation
- Real-time subscriptions (future feature)

### 4. **Simplified Deployment**
- No need to manage PostgreSQL server
- Automatic updates and maintenance
- Built-in connection pooling

## Troubleshooting

### Connection Issues

**Error**: "Missing Supabase configuration"
**Solution**: Ensure `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set in your `.env` file

**Error**: "Failed to connect to Supabase"
**Solution**: 
1. Verify your Supabase URL is correct
2. Check that your service role key is valid
3. Ensure your Supabase project is active

### Database Schema Issues

**Error**: "Table does not exist"
**Solution**: Run the schema creation script in your Supabase SQL editor

**Error**: "Permission denied"
**Solution**: Ensure you're using the `service_role` key, not the `anon` key

### Performance Considerations

- Supabase API calls have some latency compared to direct database connections
- For high-frequency operations, consider implementing caching
- Supabase automatically handles connection pooling and optimization

## Rollback Plan

If you need to rollback to PostgreSQL:

1. Revert import statements in all files:
   ```python
   from database.db_psql import UserServer, HomeworkServer, ImageServer
   ```

2. Update environment variables to use PostgreSQL credentials

3. Ensure PostgreSQL server is running and accessible

4. The legacy `db_psql.py` file is preserved for this purpose

## Support

For issues related to:
- **Supabase**: Check [Supabase documentation](https://supabase.com/docs)
- **Migration**: Review this guide and test script output
- **Application**: Check the main application logs and error messages

## Next Steps

After successful migration:

1. **Test All Features**: Verify user registration, assignment creation, and student workflows
2. **Monitor Performance**: Watch for any performance changes
3. **Update Documentation**: Update any deployment guides or documentation
4. **Consider Advanced Features**: Explore Supabase real-time features and row-level security
