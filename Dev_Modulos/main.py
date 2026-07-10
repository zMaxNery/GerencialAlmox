from view.home_page import HomePage
from core.create_database import create_database

# Start do app e mantem aberto
def main():
    create_database()
    
    app = HomePage()
    app.mainloop()

if __name__ == "__main__":
    main()
