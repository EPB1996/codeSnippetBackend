from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS
from flask_restx import fields, Resource, Api

app = Flask(__name__)
api = Api(app)

CORS(app, resources={r"/*": {"origins": "*"}})

# MongoDB connection configuration
client = MongoClient('mongodb://mongodb:27017/')
db = client['codeSnippets']
courses_collection = db['course']
snippets_collection = db["snippets"]
comments_collection = db["comments"]

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
    'tags': fields.List(fields.String)
})

comment_model = api.model("comment", {
    "user_name": fields.String(required=True, description="Comment creator"),
    "date": fields.String(required=True, description="Comment date"),
    "comment": fields.String(required=True, description="Comment"),
    "snippet_id": fields.String(required=True, description="Comment"),

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
    
    @api.expect(course_model)
    @api.doc(params={'course_id': 'A Course ID'})
    def patch(self, course_id):
        data = request.get_json()

        if not data:
            return {'message': 'Invalid input'}, 400

        # Check for null values before patching
        valid_fields = ['title', 'description']
        update_data = {}
        
        for field in valid_fields:
            if data.get(field) is not None:
                update_data[field] = data[field]
        
        print(update_data)

        result = courses_collection.update_one(
            {'_id': ObjectId(course_id)},
            {'$set': update_data}
        )

        if result.modified_count > 0:
            updated_course = courses_collection.find_one({'_id': ObjectId(course_id)})
            snippets_list = getCodeSnippetsForCourse(str(updated_course['_id']))

            return jsonify({
                'id': str(updated_course['_id']),
                'title': updated_course['title'],
                'description': updated_course['description'],
                'snippets': snippets_list
            })
        else:
            return {'message': 'Course not found'}, 404

# SNIPPETS
@api.route('/snippets')
class Snippets(Resource):
    def get(self):
        snippets = list(snippets_collection.find())
        snippets_list = []
        for snippet in snippets:
            comments = getComments(str(snippet['_id']))
            snippets_list.append({
                'id': str(snippet['_id']),
                'code': snippet['code'],
                "explanation": snippet["explanation"],
                'description': snippet['description'],
                'tags': snippet['tags'],
                'courseId': snippet["courseId"],
                'comments': comments
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
                comments = getComments(snippet_id)
                snippet_to_return = {
                    'id': str(snippet['_id']),
                    'code': snippet['code'],
                    'description': snippet['description'],
                    'tags': snippet['tags'],
                    "explanation": snippet["explanation"],
                    'courseId': snippet["courseId"],
                    "comments": comments
                }

                return snippet_to_return, 200
            else:
                return {"message": "Snippet not found"}, 404
        except Exception as e:
            return {"message": str(e)}, 500

    @api.expect(snippet_model)
    @api.doc(params={'snippet_id': 'A snippet ID'})
    def patch(self, snippet_id):
        data = request.get_json()

        if not data:
            return {'message': 'Invalid input'}, 400

        # Check for null values before patching
        valid_fields = ['code', 'description', 'tags', "explanation"]
        update_data = {}
        
        for field in valid_fields:
            if data.get(field) is not None:
                update_data[field] = data[field]

        result = snippets_collection.update_one(
            {'_id': ObjectId(snippet_id)},
            {'$set': update_data}
        )

        if result.modified_count > 0:
            updated_snippet = snippets_collection.find_one({'_id': ObjectId(snippet_id)})
            comments = getComments(snippet_id)
            snippet_to_return = {
                'id': str(updated_snippet['_id']),
                'code': updated_snippet['code'],
                'description': updated_snippet['description'],
                'tags': updated_snippet['tags'],
                'courseId': updated_snippet["courseId"],
                "explanation":updated_snippet["explanation"],
                "comments": comments
            }

            return snippet_to_return
        else:
            return {'message': 'Snippet not found'}, 404


# Comments


@api.route('/comments')
class Comments(Resource):
    def get(self):
        comments = list(comments_collection.find())
        comments_list = []
        for comment in comments:
            comments_list.append({
                'id': str(comment['_id']),
                'user_name': comment['user_name'],
                "date": comment["date"],
                'comment': comment['comment'],
                'snippet_id': comment["snippet_id"]
            })

        return jsonify(comments_list)

    @api.expect(comment_model)
    def post(self):
        data = request.get_json()

        # Ensure the "code" and "description" fields are present in the request data
        if 'user_name' not in data or 'comment' not in data:
            return {"message": "'user_name','comment' are required."}, 400

        snippet = snippets_collection.find_one(
            {"_id": ObjectId(data["snippet_id"])})

        if (snippet):
            # Insert the new comment into the collection
            result = comments_collection.insert_one(data)
            return {"message": "Comment created successfully", "id": str(result.inserted_id)}, 201
        else:
            return {"message": "Snippet Id is not valid", "snippet_id": str(data["snippet_id"])}, 404


def getCodeSnippetsForCourse(course_id):
    query = {"courseId": course_id}
    snippets = list(snippets_collection.find(
        query))

    snippets_list = []
    for snippet in snippets:
        comments = getComments(str(snippet['_id']))
        snippets_list.append({
            'id': str(snippet['_id']),
            'code': snippet['code'],
            "explanation": snippet["explanation"],
            'description': snippet['description'],
            'tags': snippet['tags'],
            'comments': comments
        })

    return snippets_list


def getComments(snippet_id: str):
    comments = comments_collection.find({"snippet_id": snippet_id})
    if comments:
        comments_to_return = [{
            "comment_id": str(comment["_id"]),
            "user_name": comment["user_name"],
            "date":comment["date"],
            "comment":comment["comment"],
            "snippet_id":comment["snippet_id"],
        } for comment in comments]
    return comments_to_return


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
