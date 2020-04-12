from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import *
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.template.defaultfilters import slugify
import docker
import os
import shutil
from django import forms
from django.core.files.storage import FileSystemStorage

CURRENT_PORT = 3000


def home(request):
    context = {}
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    if FSUser.objects.get(user=request.user).current_port is not None:
        context['current_ide_url'] = "http://localhost:{}".format(FSUser.objects.get(user=request.user).current_port)
        context['current_ide_class'] = Classroom.objects.get(classroom_code=FSUser.objects.get(user=request.user).current_class_ide).classroom_name

    context['classes_teaching'] = FSUser.objects.get(user=request.user).teacher_of.all()
    context['classes_learning'] = FSUser.objects.get(user=request.user).student_of.all()

    return render(request, 'index.html', context)


def home_process(request):
    if "r_type" in request.POST:
        if request.POST['r_type'] == "JOIN":
            room = Classroom.objects.filter(classroom_code=request.POST['classcode'])
            if len(room) != 0:
                FSUser.objects.get(user=request.user).student_of.add(room[0])
                name_string = "{}-{}".format(room[0].classroom_code,
                                             request.user.get_username())
                package_path = ""
                path_to_data = '/home/alexweiss/classroom-ide/data/{}'.format(name_string)
                path_to_teacher = '/home/alexweiss/classroom-ide/data/{}/{}'.format(room[0].teacher_code, name_string)
                os.mkdir(path_to_data)
                port_container = DockerInstances.objects.order_by('-port')[0].port + 1
                if room[0].env == Classroom.PYTHON:
                    package_path = "theiaide/theia-python"
                    shutil.copytree('/home/alexweiss/classroom-ide/examples/python-example',
                                    path_to_data + "/python-example")
                elif room[0].env == Classroom.JAVA:
                    package_path = "theiaide/theia-java"
                    shutil.copytree('/home/alexweiss/classroom-ide/examples/java-example', path_to_data + "/java-example")
                elif room[0].env == Classroom.CPP:
                    package_path = "theiaide/theia-cpp"
                    shutil.copytree('/home/alexweiss/classroom-ide/examples/cpp-example', path_to_data + "/cpp-example")
                ports_string = {"3000/tcp": port_container}
                print(ports_string)
                x = DockerInstances()
                x.port = port_container
                x.save()

                volumes = {path_to_data: {'bind': '/home/project', 'mode': 'rw'}}
                client = docker.from_env()
                client.containers.create(package_path, volumes=volumes, ports=ports_string, name=name_string, detach=True)
                return HttpResponseRedirect(reverse("class_info", kwargs={'class_id':room[0].id}))
            else:
                pass
        elif request.POST['r_type'] == "CREATE":
            room = Classroom.objects.create(
                classroom_name=request.POST['classname'],
                description="",
                env=request.POST['env']
            )
            code = room.generate_code()
            name_string = "{}-{}".format(code, request.user.get_username())
            path_to_data = '/home/alexweiss/classroom-ide/data/{}'.format(name_string)
            os.mkdir(path_to_data)
            room.teacher_code = name_string
            room.save()
            FSUser.objects.get(user=request.user).teacher_of.add(room)

            port_container = DockerInstances.objects.order_by('-port')[0].port + 1
            ports_string = {"3000/tcp": port_container}
            x = DockerInstances()
            x.port = port_container
            x.save()
            volumes = {path_to_data: {'bind': '/home/project', 'mode': 'rw'}}
            if room.env == Classroom.PYTHON:
                package_path = "theiaide/theia-python"
            elif room.env == Classroom.JAVA:
                package_path = "theiaide/theia-java"
            elif room.env == Classroom.CPP:
                package_path = "theiaide/theia-cpp"
            client = docker.from_env()
            client.containers.create(package_path, volumes=volumes, ports=ports_string, name=name_string, detach=True)
            return HttpResponseRedirect(reverse("class_info", kwargs={'class_id': room.id}))
    return HttpResponseRedirect(reverse('home'))

def class_process(request, class_id):
    user = FSUser.objects.get(user=request.user)
    if 'start_env' in request.POST:
        if user.current_port is not None:
            client = docker.from_env()
            name_string = "{}-{}".format(user.current_class_ide, request.user.get_username())
            user.current_port = None
            user.current_class_ide = None
            client.containers.get(name_string).stop()

        user.current_class_ide = Classroom.objects.get(id=class_id).classroom_code
        client = docker.from_env()

        # docker run -it --init -p 3000:3000 -v "$(pwd):/home/project:cached"
        name_string = "{}-{}".format(Classroom.objects.get(id=class_id).classroom_code, request.user.get_username())
        client.containers.get(name_string).start()
        user.current_port = int(list(client.containers.get(name_string).ports.values())[0][0]['HostPort'])

    elif 'stop_env' in request.POST:
        user.current_port = None
        user.current_class_ide = None
        client = docker.from_env()
        name_string = "{}-{}".format(Classroom.objects.get(id=class_id).classroom_code, request.user.get_username())
        client.containers.get(name_string).stop()
    elif 'new_assign' in request.POST:
        new_post = Assignment()
        new_post.classroom = Classroom.objects.get(id=class_id)
        new_post.title = request.POST['assign_name']
        new_post.description = request.POST['description']
        if request.POST['assign_due'] != "":
            new_post.due_date = request.POST['assign_due']
        new_post.folder_name = slugify(request.POST['assign_name'])
        if 'assign_attach' in request.FILES:
            attachment = request.FILES['assign_attach']
            client = docker.from_env()
            for user in FSUser.objects.all():
                if Classroom.objects.get(id=class_id) in user.student_of.all():
                    name = "{}-{}".format(Classroom.objects.get(id=class_id).classroom_code, user.user.username)
                    path_to_data = '/home/alexweiss/classroom-ide/data/{}/{}'.format(name, new_post.folder_name)
                    os.mkdir(path_to_data)
                    client.containers.get(name).put_archive("/home/project/{}".format(new_post.folder_name), attachment)
                if Classroom.objects.get(id=class_id) in user.teacher_of.all():
                    name = "{}-{}".format(Classroom.objects.get(id=class_id).classroom_code, user.user.username)
                    path_to_data = '/home/alexweiss/classroom-ide/data/{}/{}'.format(name, new_post.folder_name)
                    os.mkdir(path_to_data)
        new_post.save()
    elif 'submit_assignment' in request.POST:
        assignment = Assignment.objects.get(id=request.POST['submit_assignment'])
        x = Submission()
        x.user = user
        x.save()
        assignment.submitted_by.add(x)
        client = docker.from_env()
        name = "{}-{}".format(Classroom.objects.get(classroom_code=request.POST['submit_classroom']).classroom_code, user.user.username)
        files = client.containers.get(name).get_archive("/home/project/{}".format(assignment.folder_name))
        path_to_data = '/home/alexweiss/classroom-ide/data/{}/{}/{}'.format(assignment.classroom.teacher_code, assignment.folder_name, request.user.username)
        os.mkdir(path_to_data)
        path = "/home/project/{}/{}".format(assignment.folder_name, request.user.username)
        client.containers.get(assignment.classroom.teacher_code).put_archive(path, files[0])
        assignment.save()
    user.save()
    return HttpResponseRedirect(reverse('class_info', kwargs={"class_id": class_id}))


def class_info(request, class_id):
    global CURRENT_PORT
    context = {}
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))
    if class_id not in FSUser.objects.get(user=request.user).teacher_of.all().values_list('id', flat=True) and class_id not in FSUser.objects.get(user=request.user).student_of.all().values_list('id', flat=True):
        return HttpResponseRedirect(reverse('home'))
    if class_id in FSUser.objects.get(user=request.user).teacher_of.all().values_list('id', flat=True):
        context['teacher'] = True
    context['class'] = Classroom.objects.get(id=class_id)
    context['classes_teaching'] = FSUser.objects.get(user=request.user).teacher_of.all()
    context['classes_learning'] = FSUser.objects.get(user=request.user).student_of.all()
    user = FSUser.objects.get(user=request.user)
    context['assignments'] = Assignment.objects.filter(classroom_id=class_id).all()[::-1]
    context['submissions'] = []
    if class_id not in FSUser.objects.get(user=request.user).teacher_of.all().values_list('id', flat=True):
        for a in Assignment.objects.filter(classroom_id=class_id).all():
            if user.id in a.submitted_by.all().values_list('user', flat=True):
                context['submissions'].append(a.id)

    print(context['submissions'])

    context['fsuser'] = user
    context['class_students'] = []
    context['student_count'] = 0
    for u in FSUser.objects.all():
        if len(u.student_of.filter(id=class_id)) != 0:
            context['student_count'] += 1
            context['class_students'].append(u)

    if user.current_class_ide == Classroom.objects.get(id=class_id).classroom_code:
        context['env_url'] = "http://localhost:{}".format(user.current_port)

    return render(request, 'class.html', context)


class UserCreateForm(UserCreationForm):
    first_name = forms.CharField()
    last_name = forms.CharField()

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "password1", "password2")

    def save(self, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user

def signup(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            x = FSUser()
            x.user = user
            x.save()
            return redirect('home')
    else:
        form = UserCreateForm()
    return render(request, 'registration/register.html', {'form': form})