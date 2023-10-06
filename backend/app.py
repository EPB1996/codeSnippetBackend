from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS
from flask_restx import fields, Resource, Api

app = Flask(__name__)
api = Api(app)

CORS(app, resources={r"/": {"origins": ""}})

# MongoDB connection configuration
client = MongoClient('mongodb://mongodb:27017/')
db = client['codeSnippets']
courses_collection = db['course']
snippets_collection = db["snippets"]

# models

course_model = api.model('Course', {
    'title': fields.String(required=True, description='Course name'),
    'description': fields.String(required=True, description='Course description')
})

snippet_model = api.model('Snippet', {
    'description': fields.String(required=True, description='Snippet description'),
    'code': fields.String(required=True, description='Snippet code'),
    'explanation': fields.String(required=True, description='Snippet Code explanation'),
    'courseId': fields.String(required=True, description='Snippet Course Association'),
    'tags': fields.List(fields.String),


})


@api.route('/courses')
class Course(Resource):
    def get(self):
        try:
            courses = list(courses_collection.find())
            course_list = []
            for course in courses:
                snippets_list = []
                snippets_list = getCodeSnippetsForCourse(str(course['_id']))
                course_list.append({
                    'id': str(course['_id']),
                    'title': course['title'],
                    'description': course['description'],
                    'snippets': snippets_list
                })
            return jsonify(course_list)
        except Exception as e:
            return {"message": str(e)}, 500

    @api.expect(course_model)
    def post(self):
        data = request.get_json()
        if 'title' not in data or 'description' not in data:
            return {'message': 'Missing data'}, 400

        result = courses_collection.insert_one(data)
        return {'message': 'Course added', 'id': str(result.inserted_id)}, 200


@api.route('/courses/<string:course_id>')
class Course(Resource):
    @api.doc(params={'course_id': 'An Course ID'})
    def get(self, course_id):
        course = courses_collection.find_one({'_id': ObjectId(course_id)})

        if course:
            snippets_list = getCodeSnippetsForCourse(str(course['_id']))

            return jsonify({
                'id': str(course['_id']),
                'title': course['title'],
                'description': course['description'],
                'snippets': snippets_list
            })
        else:
            return {'message': 'Course not found'}, 404

    @api.doc(params={'course_id': 'An Course ID'})
    def delete(self, course_id):
        result = courses_collection.delete_one({'_id': ObjectId(course_id)})
        if result.deleted_count > 0:
            return {'message': 'Course deleted'}
        else:
            return {'message': 'Course not found'}, 404


def getCodeSnippetsForCourse(course_id):
    query = {"courseId": course_id}
    snippets = list(snippets_collection.find(
        query))

    snippets_list = []
    for snippet in snippets:
        snippets_list.append({
            'id': str(snippet['_id']),
            'code': snippet['code'],
            "explanation": snippet["explanation"],
            'description': snippet['description'],
            'tags': snippet['tags'],
        })

    return snippets_list


# SNIPPETS
@api.route('/snippets')
class Snippets(Resource):
    def get(self):
        snippets = list(snippets_collection.find())
        snippets_list = []
        for snippet in snippets:
            snippets_list.append({
                'id': str(snippet['_id']),
                'code': snippet['code'],
                "explanation": snippet["explanation"],
                'description': snippet['description'],
                'tags': snippet['tags'],
                'courseId': snippet["courseId"]
            })

        return jsonify(snippets_list)

    @api.expect(snippet_model)
    def post(self):
        data = request.get_json()

        # Ensure the "code" and "description" fields are present in the request data
        if 'code' not in data or 'description' not in data or "courseId" not in data:
            return {"message": "'code','description' and 'courseID' are required."}, 400

        course = courses_collection.find_one(
            {"_id": ObjectId(data["courseId"])})

        if (course):
            # Insert the new snippet into the collection
            result = snippets_collection.insert_one(data)
            return {"message": "Snippet created successfully", "id": str(result.inserted_id)}, 201
        else:
            return {"message": "CourseID is not valid", "courseId": str(data.courseId)}, 404


@api.route('/snippets/<string:snippet_id>')
class Snippets(Resource):
    @api.doc(params={'snippet_id': 'A snippet ID'})
    def get(self, snippet_id):
        try:
            snippet = snippets_collection.find_one(
                {"_id": ObjectId(snippet_id)})
            if snippet:
                snippet_to_return = {
                    'id': str(snippet['_id']),
                    'code': snippet['code'],
                    'description': snippet['description'],
                    'tags': snippet['tags'],
                    'courseId': snippet["courseId"]
                }

                return snippet_to_return, 200
            else:
                return {"message": "Snippet not found"}, 404
        except Exception as e:
            return {"message": str(e)}, 500


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
