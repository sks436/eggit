from flask_restful import Resource, Api
from app import app

from models import User

api = Api(app)

class UserResource(Resource):
    def get(self):
        users=User.query.all()
        return {'Users': [ {'Registration Number':(user.registration_number).split('_')[0], 'Name':user.name, 'Role':user.role}for user in users] }
api.add_resource(UserResource,'/api/slot')