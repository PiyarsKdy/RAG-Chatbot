from fastapi import  Depends, HTTPException, Response, APIRouter
import mysql.connector
from helpers.env_loader import rds_host, rds_port, rds_db_name, rds_user, rds_password
from helpers.sql_agent import execute_query
from helpers.session_info import *
router = APIRouter()

@router.get("/companyDetails", dependencies=[Depends(cookie)])
async def companyDetails():
    try:
        result = execute_query("SELECT company_id, name, domain, auth_key FROM company_details")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



