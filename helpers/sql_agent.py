import mysql.connector
from helpers.env_loader import rds_host, rds_port, rds_db_name, rds_user, rds_password

def execute_query(query, tuples = None, cmd = 'fetchall'):
    print(query)
    try:
        connection = mysql.connector.connect(host = rds_host,
                                                    port = rds_port,
                                                    database = rds_db_name,
                                                    user = rds_user,
                                                    password = rds_password)
        cursor = connection.cursor()

        cursor.execute(query, tuples)
        if cmd == 'fetchall':
            results = cursor.fetchall()
        elif cmd == 'fetchone':
            results = cursor.fetchone()
        elif cmd == 'commit':
            connection.commit()
            results = None
    except Exception as e:
        return{"message": str(e)}
    finally:
        cursor.close()
        connection.close()
    return results