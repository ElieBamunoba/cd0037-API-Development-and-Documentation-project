import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app)
    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        return response
    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions')
    def get_questions():
        # Implement pagination
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * 10
        end = start + 10

        questions = Question.query.all()
        categories= categories=Category.query.all()
        formatted_questions = [question.format() for question in questions]
        return jsonify({
            'success': True,
            'plants':formatted_questions[start:end],
            'total_plants':len(formatted_questions), 
            'categories':toDict(categories),
            })

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.
    """
    @app.route('/questions/<int:question_id>' , methods=['DELETE'])
    def delete_question(question_id):
        try:
            question=Question.query.filter_by(id=question_id).one_or_none()
            if question is None:
                abort(404)
            question.delete()
            questions=Question.query.order_by(Question.id).all()
            categories=Category.query.all()
            paginated_questions=paginate_items(request, questions)
            return jsonify({
                'success':True,
                'deleted':question_id,
                'questions':paginated_questions,
                'total_questions':len(questions),
                'categories':toDict(categories),
        
            })
        except:
            abort(422)
        
    """
    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions', methods=['POST'])
    def create_question():
        new_question=request.get_json()['question']
        new_answer=request.get_json()['answer']
        new_difficulty=request.get_json()['difficulty']
        new_category=request.get_json()['category']
        question=Question(
            question=new_question,
            answer=new_answer,
            difficulty=new_difficulty,
            category=new_category)
        #Ensure no null field
        if (new_answer and new_category and new_difficulty and new_question):
            try:
                question.insert()
                questions=Question.query.order_by(Question.id).all()
                categories=Category.query.all()
                paginated_questions=paginate_items(request, questions)
                if len(paginated_questions)==0:
                    abort(404)
                return jsonify({
                    'success':True,
                    'created':question.id,
                    'questions':paginated_questions,
                    'total_questions':len(questions),
                    'categories':toDict(categories),
                    'current_category':None
                })
            except:
                #clear pending transactions
                question.rollback()
                abort(422)
            finally:
            # close session to free up system resources
                question.close()
        
        else:
            abort(400)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/questions/search' , methods=['POST'])
    def search_question():
        search_term= request.get_json().get('searchTerm')
        # make search input required
        if search_term:
            results=Question.query.filter(Question.question.ilike(f'%{(search_term)}%')).all()
            categories=Category.query.all()
            paginated_questions=paginate_items(request, results)
            if len(paginated_questions)==0:
                abort(404)
            return jsonify({
                'success':True,
                'searchTerm':search_term,
                'questions':paginated_questions,
                'total_questions':len(results),
                'categories':toDict(categories),
                'current_category': null
            })
        else:
            abort(400)
        
    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions')
    def Get_categories(category_id):
        questions=Question.query.filter_by(category=category_id).all()
        categories=Category.query.all()
        paginated_questions=paginate_items(request, questions)
        if len(paginated_questions)==0:
            abort(404)
        return jsonify({
            'success':True,
            'questions':paginated_questions,
            'total_questions':len(questions),
            'categories':toDict(categories) ,
            'current_category': category_id
        })
    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def quiz():
        #gets quiz category and previous questions
        category=request.get_json()['quiz_category']
        previous_questions=request.get_json()['previous_questions']
        if previous_questions is None:
            abort(500)
        if ('quiz_category' and 'previous_questions') not in request.get_json():
            abort(400)
        if category['id']==0:
            questions=Question.query.all()
        else:
            questions=Question.query.filter_by(category=category['id']).all()
        #creates a list of formated questions with id not in previous questions
        list_of_valid_questions=[
            question.format()
            for question in questions
            if (question.id not in previous_questions)
            ]
        if len(list_of_valid_questions)!=0:
        # generates a random index 
            next_question_index = random.randrange(0, len(list_of_valid_questions))
        # picks a next question
            next_question=list_of_valid_questions[next_question_index]
        elif len(list_of_valid_questions)==0:
        # Notifies the frontend to end quiz if no new question left
            next_question=None
        return jsonify({
            'success': True,
            'question':next_question,
            'previousQuestions':previous_questions
        })
        
    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'Bad request'
        }),400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'resource not found'
        }), 404

    @app.errorhandler(422)
    def not_processable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'could not process recource'
        }), 422
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': 'internal server error'
        }), 500

    return app

