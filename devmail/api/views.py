from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

import bcrypt
import base64

from rest_framework import status
from rest_framework.response import Response
from .models import User, Mail
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django.db.models import Q
from .serializers import UserSerializer, RegisterUserSerializer, \
    LoginUserSerializer, MailSerializer, SendMailSerializer, \
    DetailSerialzer


# Create your views here.


class ListUsers(ListAPIView):

    queryset = User.objects.all()
    serializer_class = UserSerializer


class RegisterUser(APIView):

    serializer_class = RegisterUserSerializer

    def post(self, request, format=None):

        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():

            return Response(data={"Error": "Invalid Data"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()

        first_name = serializer.data.get('first_name')
        last_name = serializer.data.get('last_name')
        username = serializer.data.get('username')
        password = serializer.data.get('password')
        accept_promotions = serializer.data.get('accept_promotions')

        password = bcrypt.hashpw(password, bcrypt.gensalt(12))
        queryset = User.objects.filter(username=username)

        if queryset.exists():
            return Response({"Error": "User Already Exists"},
                            status=status.HTTP_409_CONFLICT)
        user = User(first_name=first_name, last_name=last_name,
                    username=username, password=password,
                    accept_promotions=accept_promotions)
        user.save()

        self.request.session['username'] = username
        self.request.session.set_expiry(0)

        return Response({"Success": "User Added"},
                        status=status.HTTP_200_OK)


class GetLogin(APIView):

    def get(self, request, format=None):

        if not self.request.session.exists(self.request.session.session_key):

            return Response(data={"Error": "Not logged in"},
                            status=status.HTTP_401_UNAUTHORIZED)
        return Response(data={"Success": "Logged In"},
                        status=status.HTTP_202_ACCEPTED)


class LoginUser(APIView):

    serializer_class = LoginUserSerializer

    def post(self, request, format=None):

        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():

            return Response(data={"Error": "Invalid Data"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        username = serializer.data.get('username')
        password = serializer.data.get('password')
        remember = serializer.data.get('remember')

        queryset = User.objects.filter(username=username)

        if not queryset.exists():

            return Response(data={"Error": "User Not Found"},
                            status=status.HTTP_401_UNAUTHORIZED)

        user = queryset[0]
        hashed_password = user.password

        if not bcrypt.checkpw(password, hashed_password):

            return Response(data={"Error": "Wrong Credentials"},
                            status=status.HTTP_400_BAD_REQUEST)

        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()
            self.request.session['username'] = username
            if not remember:
                self.request.session.set_expiry(0)

        return Response(data={"Success": "Logged In"},
                        status=status.HTTP_202_ACCEPTED)


class ListMails(APIView):

    serializer_class = MailSerializer

    def get(self, request, format=None):

        queryset = Mail.objects.filter(
            receiver=self.request.session['username'])

        data = []

        for entry in queryset:

            data.append(self.serializer_class(entry).data)

        return Response(data={"data": data}, status=status.HTTP_200_OK)


class LogoutUser(APIView):

    def get(self, request, format=None):

        if self.request.session.exists(self.request.session.session_key):
            self.request.session.flush()
            return Response(data={"Success": "Logged Out"},
                            status=status.HTTP_200_OK)

        return Response(data={"Error": "Not logged in"},
                        status=status.HTTP_401_UNAUTHORIZED)


class SendMail(APIView):

    serializer_class = SendMailSerializer

    def post(self, request, format=None):

        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():

            return Response(data={"Error": "Invalid Data"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        to = serializer.data.get('to')
        subject = serializer.data.get('subject')
        message = serializer.data.get('message')

        mail = Mail(sender=self.request.session['username'],
                    receiver=to, subject=subject, message=message)

        mail.save()

        return Response({"Success": "User Added"},
                        status=status.HTTP_200_OK)


class DetailMail(APIView):

    serializer_class = DetailSerialzer

    def get(self, request, format=None, *args, **kwargs):

        decoded = str(base64.b64decode(kwargs['slug']))
        id = int(decoded.split("<===>", 2)[1])

        queryset = Mail.objects.filter(id=id)

        if not queryset.exists():

            return Response(data={"Error": "Wrong request"},
                            status=status.HTTP_400_BAD_REQUEST)

        data = self.serializer_class(queryset[0]).data

        return Response({"Success": data},
                        status=status.HTTP_200_OK)


class SentMails(APIView):

    serializer_class = MailSerializer

    def get(self, request, format=None):

        queryset = Mail.objects.filter(
            sender=self.request.session['username'])

        data = []

        for entry in queryset:

            data.append(self.serializer_class(entry).data)

        return Response(data={"data": data}, status=status.HTTP_200_OK)


class SearchMails(APIView):

    serializer_class = MailSerializer

    def get(self, request, format=None, *args, **kwargs):

        string = kwargs['string'].split('-')

        if string[0] == 'r':

            queryset = Mail.objects.filter(
                Q(receiver=self.request.session['username']) &
                (Q(subject__icontains=string[1]) |
                 Q(message__icontains=string[1])))

        elif string[0] == 's':
            queryset = Mail.objects.filter(
                Q(sender=self.request.session['username']) &
                (Q(subject__icontains=string[1]) |
                 Q(message__icontains=string[1])))
        else:
            return Response(data={'Error': "Wrong String"},
                            status=status.HTTP_400_BAD_REQUEST)

        data = []

        for entry in queryset:

            data.append(self.serializer_class(entry).data)

        return Response(data={"data": data}, status=status.HTTP_200_OK)
