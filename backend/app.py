from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

# MongoDB connection configuration
client = MongoClient('mongodb://mongodb:27017/')
db = client['codeSnippets']
courses_collection = db['course']

# Define a Course class


class Course:
    def __init__(self, title, description, snippets):
        self.title = title
        self.description = description
        self.snippets = snippets

# Routes


@app.route('/courses', methods=['GET'])
def get_courses():
    courses = list(courses_collection.find())
    course_list = []
    for course in courses:
        course_list.append({
            'id': str(course['_id']),
            'title': course['title'],
            'description': course['description'],
            'snippets': course['snippets']
        })
    return jsonify(course_list)


@app.route('/courses/<string:course_id>', methods=['GET'])
def get_course(course_id):
    course = courses_collection.find_one({'_id': ObjectId(course_id)})
    if course:
        return jsonify({
            'id': str(course['_id']),
            'title': course['title'],
            'description': course['description'],
            'snippets': course['snippets']
        })
    else:
        return jsonify({'message': 'Course not found'}), 404


@app.route('/courses', methods=['POST'])
def add_course():
    data = request.get_json()
    if 'title' not in data or 'description' not in data:
        return jsonify({'message': 'Missing data'}), 400

    new_course = Course(data['title'], data['description'], data['snippets'])
    course_data = {
        'title': new_course.title,
        'description': new_course.description,
        'snippets': new_course['snippets']
    }
    result = courses_collection.insert_one(course_data)
    return jsonify({'message': 'Course added', 'id': str(result.inserted_id)})


@app.route('/courses/<string:course_id>', methods=['PUT'])
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
        return jsonify({'message': 'Course not found'}), 404


@app.route('/courses/<string:course_id>', methods=['DELETE'])
def delete_course(course_id):
    result = courses_collection.delete_one({'_id': ObjectId(course_id)})
    if result.deleted_count > 0:
        return jsonify({'message': 'Course deleted'})
    else:
        return jsonify({'message': 'Course not found'}), 404


if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0")
