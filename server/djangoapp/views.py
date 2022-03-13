from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarDealer, CarModel
from .restapis import get_dealer_by_id, get_dealers_from_cf, get_dealer_reviews_from_cf, post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
from django.template import loader
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Create your views here.
# Create an `about` view to render a static about page
def about(request):
    return render(request, 'djangoapp/aboutus.html')

# Create a `contact` view to return a static contact page
def contact(request):
    return render(request, 'djangoapp/contactus.html')

# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            return render(request, 'djangoapp/user_login.html', context)
    else:
        return render(request, 'djangoapp/user_login.html', context)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    print("Log out the user `{}`".format(request.user.username))
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.debug("{} is new user".format(username))
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else:
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    context={}
    if request.method == "GET":
        url = "https://761bcee5.us-south.apigw.appdomain.cloud/api/dealership"
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(url)
        context = {
            'dealership_list': dealerships,
        }
        return render(request, 'djangoapp/index.html', context)

# Create a `get_dealer_details` view to render the reviews of a dealer
# def get_dealer_details(request, dealer_id):
def get_dealer_details(request, dealer_id):
    context={}
    if request.method == "GET":
        url = "https://761bcee5.us-south.apigw.appdomain.cloud/api/review"
        reviews = get_dealer_reviews_from_cf(url, dealer_id=dealer_id)
        dealer_url = "https://761bcee5.us-south.apigw.appdomain.cloud/api/dealership"
        dealer = get_dealer_by_id(dealer_url, dealer_id=dealer_id)
        context = {
            'review_list': reviews,
            'dealer': dealer
        }
        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    context={}
    review={}
    json_payload={}
    url="https://761bcee5.us-south.apigw.appdomain.cloud/api/review"
    
    if request.user.is_authenticated:
        if request.method == "GET":
            dealer_url = "https://761bcee5.us-south.apigw.appdomain.cloud/api/dealership"
            dealer = get_dealer_by_id(dealer_url, dealer_id=dealer_id)
            cars= CarModel.objects.all().filter(dealer_id=dealer_id)
            context = {
                'cars': cars,
                'dealer': dealer
            }
            return render (request, 'djangoapp/add_review.html', context)
        elif request.method == "POST":
            car = CarModel.objects.get(pk=request.POST['car'][0])
            print(car)

            review["car_model"] = car.name
            review["car_make"] = car.car_make.name
            review["car_year"] = car.year.strftime("%Y")
            review["dealership"] = dealer_id
            review["time"] = datetime.utcnow().isoformat()
            #Hard code as this required when populate details
            review["name"] = "Jammy Patderson"
            review["purchase"] = 'purchasecheck' in request.POST
            if review["purchase"] and (request.POST['purchasedate'] is not None):
                review["purchase_date"] = request.POST['purchasedate']
            else:
                review["purchase_date"] = " "
            review["review"] =  request.POST['content']

            json_payload = {"review" : review}
            result = post_request(url, json_payload, dealerId=dealer_id)
            print(result)
            return redirect("djangoapp:dealer_details", dealer_id=dealer_id)
    else:
        return render(request, 'djangoapp/user_login.html', context)

    
