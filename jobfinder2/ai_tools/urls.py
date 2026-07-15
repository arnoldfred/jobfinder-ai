from django.urls import path
from . import views
app_name = 'ai_tools'
urlpatterns = [
    path('',                      views.tools_page,          name='tools'),
    path('chat/',                 views.chat,                name='chat'),
    path('cv/analyze/',           views.analyze_cv,          name='analyze_cv'),
    path('cv/import/',            views.import_cv,           name='import_cv'),
    path('chances/',              views.estimate_chances,    name='chances'),
    path('interview/questions/',  views.interview_questions, name='interview_q'),
    path('interview/evaluate/',   views.evaluate_answer,     name='evaluate'),
    path('salary/',               views.salary_advice,       name='salary'),
    path('job/analyze/',          views.analyze_job,         name='analyze_job'),
    path('email/',                views.draft_email,         name='email'),
    path('career/',               views.career_path,         name='career'),
    path('doc/<str:doc_type>/',   views.generate_doc,        name='generate_doc'),
    path('pdf/',                  views.generate_pdf,        name='generate_pdf'),
    path('docx/',                 views.generate_docx,       name='generate_docx'),
]
