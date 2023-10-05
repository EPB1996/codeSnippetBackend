import sys
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

# MongoDB connection configuration
client = MongoClient('mongodb://mongodb:27017/')
db = client['codeSnippets']
courses_collection = db['course']
snippets_collection = db["snippets"]

# Routes

@app.route('/courses', methods=['GET'])
def get_courses():
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
        return jsonify({"message": str(e)}), 500


@app.route('/courses/<string:course_id>', methods=['GET'])
def get_course(course_id):

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
        return jsonify({'message': 'Course not found'}), 404


def getCodeSnippetsForCourse(course_id):
    query = {"courseId": course_id}
    snippets = list(snippets_collection.find(
        query))

    snippets_list = []
    for snippet in snippets:
        snippets_list.append({
            'id': str(snippet['_id']),
            'code': snippet['code'],
            'description': snippet['description'],
            'tags': snippet['tags'],
        })

    return snippets_list


@app.route('/courses', methods=['POST'])
def add_course():
    data = request.get_json()
    if 'title' not in data or 'description' not in data:
        return jsonify({'message': 'Missing data'}), 400

    result = courses_collection.insert_one(data)
    return jsonify({'message': 'Course added', 'id': str(result.inserted_id)})


""" @app.route('/courses/<string:course_id>', methods=['PUT'])
def update_course(course_id):
    data = request.get_json()
    if 'title' not in data or 'description' not in data:
        return jsonify({'message': 'Missing data'}), 400

    updated_course = {
        'title': data['title'],
        'description': data['description'],
        'snippets': data['snippets']

    }

    result = courses_collection.update_one(
        {'_id': ObjectId(course_id)}, {'$set': updated_course})

    if result.modified_count > 0:
        return jsonify({'message': 'Course updated'})
    else:
        return jsonify({'message': 'Course not found'}), 404 """


@app.route('/courses/<string:course_id>', methods=['DELETE'])
def delete_course(course_id):
    result = courses_collection.delete_one({'_id': ObjectId(course_id)})
    if result.deleted_count > 0:
        return jsonify({'message': 'Course deleted'})
    else:
        return jsonify({'message': 'Course not found'}), 404

# Route to create a new snippet


# SNIPPETS

@app.route('/snippets', methods=['POST'])
def create_snippet():
    try:
        data = request.get_json()
        # Ensure the "code" and "description" fields are present in the request data
        if 'code' not in data or 'description' not in data or "courseId" not in data:
            return jsonify({"message": "'code','description' and 'courseID' are required."}), 400

        course = courses_collection.find_one(
            {"_id": ObjectId(data["courseId"])})
        if (course):
            # Insert the new snippet into the collection
            result = snippets_collection.insert_one(data)
            return jsonify({"message": "Snippet created successfully", "id": str(result.inserted_id)}), 201
        else:
            return jsonify({"message": "CourseID is not valid", "courseId": str(data.course)}), 404
    except Exception as e:
        return jsonify({"message": str(e)}), 500

# Route to retrieve a snippet by its ID


@app.route('/snippets/<string:id>', methods=['GET'])
def get_snippet(id):
    try:
        snippet = snippets_collection.find_one({"_id": ObjectId(id)})
        if snippet:
            snippet_to_return = {
                'id': str(snippet['_id']),
                'code': snippet['code'],
                'description': snippet['description'],
                'tags': snippet['tags'],
                'courseId': snippet["courseId"]
            }

            return jsonify(snippet_to_return), 200
        else:
            return jsonify({"message": "Snippet not found"}), 404
    except Exception as e:
        return jsonify({"message": str(e)}), 500

# Route to retrieve all snippets


@app.route('/snippets', methods=['GET'])
def get_all_snippets():
    snippets = list(snippets_collection.find())
    snippets_list = []
    for snippet in snippets:
        snippets_list.append({
            'id': str(snippet['_id']),
            'code': snippet['code'],
            'description': snippet['description'],
            'tags': snippet['tags'],
            'courseId': snippet["courseId"]
        })

    return jsonify(snippets_list)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
