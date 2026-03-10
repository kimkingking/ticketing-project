from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter()

@router.get("/list")
def get_list(db: Session = Depends(get_db)):
    try:
        list_sql = text("""
            SELECT strNumber, strSubject, strName, writeDate, strContent 
            FROM board 
            ORDER BY strNumber DESC
        """)
        result = db.execute(list_sql).fetchall()
        
        posts = []
        for row in result:
            posts.append({
                "strNumber": row[0],
                "strSubject": row[1],
                "strName": row[2],
                "writeDate": str(row[3]),
                "strContent": row[4]
            })
        return posts
    except Exception as e:
        print(e.args)
        return {"status": "fail", "message": "게시글 목록을 불러오는데 실패하였습니다."}

@router.post("/write")
def write_post(
    name: str = Form(...), 
    pw: str = Form(...), 
    subject: str = Form(...), 
    content: str = Form(...), 
    db: Session = Depends(get_db)
):
    try:
        write_sql = text("""
            INSERT INTO board (strName, strPassword, strSubject, strContent, htmlTag, writeDate) 
            VALUES (:name, :pw, :subject, :content, '', NOW())
        """)
        db.execute(write_sql, {"name": name, "pw": pw, "subject": subject, "content": content})
        db.commit()
        return {"status": "success"}
    except Exception as e:
        print(e.args)
        return {"status": "fail", "message": "게시글 작성에 실패하였습니다."}

@router.post("/update")
def update_post(
    no: int = Form(...),
    pw: str = Form(...),
    subject: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        update_sql = text("""
            UPDATE board 
            SET strSubject = :subject, strContent = :content 
            WHERE strNumber = :no AND strPassword = :pw
        """)
        result = db.execute(update_sql, {
            "no": no, 
            "pw": pw, 
            "subject": subject, 
            "content": content
        })
        db.commit()
        
        if result.rowcount == 0:
            return {"status": "fail", "message": "비밀번호가 틀렸거나 게시글이 없습니다."}
        return {"status": "success", "message": "수정 완료"}
    except Exception as e:
        print(e.args)
        return {"status": "fail", "message": "게시글 수정에 실패하였습니다."}

@router.post("/delete")
def delete_post(
    no: int = Form(...), 
    pw: str = Form(...), 
    db: Session = Depends(get_db)
):
    try:
        delete_sql = text("""
            DELETE FROM board 
            WHERE strNumber = :no AND strPassword = :pw
        """)
        result = db.execute(delete_sql, {"no": no, "pw": pw})
        db.commit()
        
        if result.rowcount == 0:
            return {"status": "fail", "message": "비밀번호가 일치하지 않습니다."}
        return {"status": "success", "message": "삭제 완료"}
    except Exception as e:
        print(e.args)
        return {"status": "fail", "message": "게시글 삭제에 실패하였습니다."}