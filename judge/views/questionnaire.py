from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse
from judge.forms import QuestionnaireForm, QuestionForm, AddQuestionForm, AddResponseForm
from judge.utils.views import generic_message
from judge.models.questionnaire import Questionnaire, Question, CorrectAnswers, SubmissionAnswers
from judge.models.contest import Contest
from django.conf import settings
from django.http import FileResponse
import os

class QuestionnaireView(View):
    template_name = 'questionnaire.html'

    def get(self, request):
        title = 'Nuevo cuestionario';
        form = QuestionnaireForm()
        return render(request, self.template_name, {'form': form, 'title': title})

    def post(self, request):
        form = QuestionnaireForm(request.POST)
        if form.is_valid():
            new_questionnaire = Questionnaire(
                name=request.POST.get('name')
            )
            new_questionnaire.save()
            return generic_message(request, 'Cuestionario añadido correctamente', 'Cuestionario Añadido')
        return render(request, self.template_name, {'form': form})


class QuestionView(View):
    template_name = 'question.html'

    def get(self, request):
        questionnaires = Questionnaire.objects.all()
        context = {
            'questionnaires': questionnaires,
            'form': QuestionForm(),
            'title': 'Nueva pregunta'
        }
        return render(request, self.template_name, context)
    def post(self, request):
        form = QuestionForm(request.POST, request.FILES)
        if form.is_valid():
            options = []
            for i in range(int(request.POST.get('options_quantity'))):
                options.append(request.POST.get('options_option_'+str(i+1)))
            new_question = Question(
                name=request.POST.get('name'),
                file=request.FILES.get('statement'),
                questionnaire_id=request.POST.get('questionnaire_name'),
                type_question=request.POST.get('type_question'),
                options=options,
                entries_quantity=request.POST.get('number_answers')
            )
            
            new_question.save()
            answers = []
            for i in range(int(request.POST.get('number_answers'))):
                answers.append(request.POST.get('answer_'+str(i+1)))

            id_question = Question.objects.latest('id').id
            new_correct_answers = CorrectAnswers(
                question_id=id_question,
                answer=answers
            )
            new_correct_answers.save()
            return generic_message(request, 'Pregunta añadida correctamente', 'Pregunta Añadida')
        print(form.errors.as_data())
        return render(request, self.template_name, {'form': form})

class AddQuestionView(View):
    template_name = 'add_question.html'

    def get(self, request):
        contest = Contest.objects.all()
        questions = Question.objects.all()
        context = {
            'form': AddQuestionForm(),
            'contests': contest,
            'questions': questions,
            'title': 'Añadir pregunta a concurso'
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        
        form = AddQuestionForm(request.POST)
        if form.is_valid():
            
            contest = Contest.objects.filter(name=request.POST.get('selected_contest')).first()
            question = Question.objects.filter(name=request.POST.get('selected_question')).first()
            if contest.questions_ids:
                question_ids = set(contest.questions_ids)
            else:
                question_ids = set()
                contest.questions_ids = []
            if request.POST.get('selected_type') == 'Add':
                if int(question.id) in question_ids:
                    return generic_message(request, 'La pregunta ya está en el concurso', 'Pregunta Añadida')  
                else:
                    contest.questions_ids.append(int(question.id))
            elif request.POST.get('selected_type') == 'Remove':
                if int(question.id) not in question_ids:
                    return generic_message(request, 'La pregunta no está en el concurso', 'Pregunta Eliminada')
                else:
                    contest.questions_ids.remove(int(question.id))
            contest.save()
            return generic_message(request, 'Pregunta añadida o eliminada correctamente', 'Pregunta Añadida o Eliminada')
        print(form.errors.as_data())
        return render(request, self.template_name, {'form': form})

class AddResponseView(View):
    template_name = 'question_response.html'

    def get(self, request, *args, **kwargs):
        contest_id = kwargs.get('contest')
        question_id = kwargs.get('question')
        title = 'Añadir respuesta'
        contest = Contest.objects.filter(id=contest_id).first()
        question = Question.objects.filter(id=question_id).first()
        name_file = question.file.name[15:]
        question_type = question.type_question
        entries_quantity = question.entries_quantity
        options = [(option, option) for option in question.options] if question.options else []

        form = AddResponseForm(question_type=question_type, options=options, entries_quantity=entries_quantity)
        current_url = request.build_absolute_uri()
        ids = contest.questions_ids
        size = max(ids)
        boolean_vector = [False]*(size+1)
        for i in ids:
            submission = SubmissionAnswers.objects.filter(name_user=request.user.username, question_id=i, user_id=request.user.id).first()
            if submission:
                if submission.correct:
                    boolean_vector[i] = True
        
        all_questions = []
        for i in ids:
            submission = SubmissionAnswers.objects.filter(name_user=request.user.username, question_id=i, user_id=request.user.id).first()
            if submission:
                if submission.correct:
                    all_questions.append((True))
                else:
                    all_questions.append((False))
            else:
                all_questions.append((False))
        if all(all_questions):
            return generic_message(request, 'Ya has respondido todas las preguntas correctamente', 'Todas las preguntas respondidas')

        absolute_url = os.path.join(settings.MEDIA_ROOT, question.file.name)
        return render(request, self.template_name, {'form': form, 'title': title, 'contest': contest, 'question': question, 'currrent_url': current_url, 'boolean_vector': boolean_vector, 'name_file': name_file, 'question_type': question_type, 'entries_quantity': entries_quantity, 'options': options, 'absolute_url': absolute_url})

    def post(self, request, *args, **kwargs):
        contest_id = kwargs.get('contest')
        question_id = kwargs.get('question')
        contest = Contest.objects.filter(id=contest_id).first()
        question = Question.objects.filter(id=question_id).first()
        form = AddResponseForm(request.POST)
        user = self.request.user
        title = 'Añadir respuesta'
        if form.is_valid():
            if question.type_question == 'options':
                answer = request.POST.get('selected_option')
                if answer == CorrectAnswers.objects.filter(question_id=question_id).first().answer[0]:
                    if SubmissionAnswers.objects.filter(name_user=user.username, name_question=question.name, user_id=user.id).first():
                        answer_creada = SubmissionAnswers.objects.filter(name_user=user.username, name_question=question.name, user_id=user.id).first()
                        answer_creada.answer = answer
                        answer_creada.correct = True
                        answer_creada.save()
                    else :
                        correct = True
                        new_response = SubmissionAnswers(
                            name_user=user.username,
                            name_question=question.name,
                            question_id=question_id,
                            user_id=user.id,
                            answer=answer,
                            correct=correct
                        )
                        new_response.save()
                else:
                    if SubmissionAnswers.objects.filter(name_user=user.username, name_question=question.name, user_id=user.id).first():
                        new_answer = SubmissionAnswers.objects.filter(name_user=user.username, name_question=question.name, user_id=user.id).first()
                        new_answer.answer = answer
                        new_answer.correct = False
                        new_answer.save()
                    else :
                        correct = False
                        new_response = SubmissionAnswers(
                            name_user=user.username,
                            name_question=question.name,
                            question_id=question_id,
                            user_id=user.id,
                            answer=answer,
                            correct=correct
                        )
                        new_response.save()
            elif question.type_question == 'development':
                correct_answers_validate = CorrectAnswers.objects.filter(question_id=question_id).first().answer
                correct_answers = []
                answers = []
                for i in range(int(question.entries_quantity)):
                    answer = request.POST.get('development_answer_'+str(i+1))
                    answers.append(answer)
                    if answer == correct_answers_validate[i]:
                        correct_answers.append(True)
                    else:
                        correct_answers.append(False)
                if correct_answers == [True]*question.entries_quantity:
                    if SubmissionAnswers.objects.filter(name_user=user.username, name_question=question.name, user_id=user.id).first():
                        new_answer = SubmissionAnswers.objects.filter(name_user=user.username, name_question=question.name, user_id=user.id).first()
                        new_answer.answer = answers
                        new_answer.correct = True
                        new_answer.save()
                    else :
                        correct = True
                        new_response = SubmissionAnswers(
                            name_user=user.username,
                            name_question=question.name,
                            question_id=question_id,
                            user_id=user.id,
                            answer=answers,
                            correct=correct
                        )
                        new_response.save()
                else:
                    if SubmissionAnswers.objects.filter(name_user=user.username, name_question=question.name, user_id=user.id).first():
                        new_answer = SubmissionAnswers.objects.filter(name_user=user.username, name_question=question.name, user_id=user.id).first()
                        new_answer.answer = answers
                        new_answer.correct = False
                        new_answer.save()
                    else :
                        correct = False
                        new_response = SubmissionAnswers(
                            name_user=user.username,
                            name_question=question.name,
                            question_id=question_id,
                            user_id=user.id,
                            answer=answers,
                            correct=correct
                        )
                        new_response.save()
            return generic_message(request, 'Respuesta añadida correctamente', 'Respuesta Añadida')
        print(form.errors.as_data())
        current_url = request.build_absolute_uri()
        ids = contest.questions_ids
        size = max(ids)
        boolean_vector = [False]*(size+1)
        for i in ids:
            submission = SubmissionAnswers.objects.filter(name_user=request.user.username, question_id=i, user_id=request.user.id).first()
            if submission:
                if submission.correct:
                    boolean_vector[i] = True
        name_file = question.file.name[15:]
        absolute_url = os.path.join(settings.MEDIA_ROOT, question.file.name)
        return render(request, self.template_name, {'form': form, 'title': title, 'contest': contest, 'question': question, 'current_url': current_url, 'boolean_vector': boolean_vector, 'name_file': name_file, 'absolute_url': absolute_url})
    
def serve_file(request, file_path):
    file_path = os.path.join(settings.BASE_DIR, file_path)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    else:
        return HttpResponse("El archivo no existe", status=404)