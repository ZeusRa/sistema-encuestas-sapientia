from app.database import SesionLocal
from app.modelos import TransaccionEncuesta
import sys

def check_transactions():
    db = SesionLocal()
    try:
        count = db.query(TransaccionEncuesta).filter(TransaccionEncuesta.id_encuesta == 33).count()
        print(f"Transactions for Survey 33: {count}")
    finally:
        db.close()

if __name__ == "__main__":
    check_transactions()
