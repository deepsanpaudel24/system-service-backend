from app.main import app

if __name__ == "__main__":
  from db import mongo
  mongo.init_app(app)
  app.run()
