import markdown
import openai
import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from projectManager.forms import ProjectForm
from subscriptions.models import StripeCustomer

from django.urls import reverse

@login_required
def home(request):
    return render(request, 'home.html')


@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)


@csrf_exempt
def create_checkout_session(request):
    if request.method == 'GET':
        domain_url = 'http://localhost:8000/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=request.user.id if request.user.is_authenticated else None,
                success_url=domain_url + 'stripe/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'cancel/',
                payment_method_types=['card'],
                mode='subscription',
                line_items=[
                    {
                        'price': settings.STRIPE_PRICE_ID,
                        'quantity': 1,
                    }
                ]
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})

@login_required(login_url='/login')
def success(request):
    return render(request, 'success.html')


@login_required(login_url='/login')
def cancel(request):
    return render(request, 'cancel.html')


@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Fetch all the required data from session
        client_reference_id = session.get('client_reference_id')
        stripe_customer_id = session.get('customer')
        stripe_subscription_id = session.get('subscription')

        # Get the user and create a new StripeCustomer
        user = User.objects.get(id=client_reference_id)
        StripeCustomer.objects.create(
            user=user,
            stripeCustomerId=stripe_customer_id,
            stripeSubscriptionId=stripe_subscription_id,
        )
        print(user.username + ' just subscribed.')

    return HttpResponse(status=200)

@login_required
def home(request):
    try:
        # Retrieve the subscription & product
        stripe_customer = StripeCustomer.objects.get(user=request.user)
        if stripe_customer.stripeSubscriptionId:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
            product = stripe.Product.retrieve(subscription.plan.product)

            return render(request, 'home.html', {
                'subscription': subscription,
                'product': product,
            })
        else:
            return render(request, 'home.html')

    except StripeCustomer.DoesNotExist:
        return render(request, 'home.html')

def require_stripe_customer(view_func):
    def wrapper(request, *args, **kwargs):
        try:
            stripe_customer = StripeCustomer.objects.get(user=request.user)
        except StripeCustomer.DoesNotExist:
            return redirect('/stripe')

        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
            if subscription.status == "active":
                return view_func(request, *args, **kwargs)
        except stripe.error.StripeError:
            pass

        return redirect('/stripe')

    return wrapper

openai.api_key = settings.OPENAI_API_KEY

@login_required(login_url='/login')
@require_stripe_customer
def result(request):
    if request.method == 'POST':
        form_test = ProjectForm(request.POST)
        if form_test.is_valid():
            description = form_test.cleaned_data["description"]
            name = form_test.cleaned_data["name"]
            skill = form_test.cleaned_data["skill"]
            weekly = form_test.cleaned_data["weekly"]
            other = form_test.cleaned_data["other"]
            deadline = form_test.cleaned_data["deadline"]
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=generate_prompt(description, name, skill, weekly, other, deadline),
                max_tokens=500,
                temperature=0.6,
            )

            all_texts = []
            for choice in response['choices']:
                text = choice['text']
                all_texts.append(text)

            result = ""
            for text in all_texts:
                result += text

            html_content = markdown.markdown(result, extensions=['markdown.extensions.tables'])
            print(html_content)
            html_content_with_styles = html_content.replace('<p>', '<p style="font-size: 1.25rem; color: #718096; padding-left: 2rem;">').replace('<h2>', '<h2 style="color: #1a202c; font-size: 2.25rem; padding-left: 2rem; margin-bottom: 0.5rem;">').replace('<ol>', '<ol style="padding-left: 3rem; margin-top: 0.5rem; line-height: 1.5; list-style-type: decimal; list-style-position: inside;">').replace('<ul>', '<ul style="max-width: 20rem; line-height: 1.5; color: #718096; list-style-type: disc; list-style-position: inside; padding-left: 2rem;">').replace('<h1>', '<h1 style="font-weight: 900; font-size: 2.25rem; text-align: center; margin-top: 6.25rem; padding: 0.5rem 0;">').replace('<tbody>', '<tbody style="background-color: #F3F4F6;">').replace('<tr>', '<tr style="background-color: #F9FAFB;">').replace('<td>', '<td style="padding: 8px;">').replace('<table>', '<table style="background-color: #D1D5DB; width: 50%; margin: 2rem;">').replace('<th>', '<th style="padding: 8px; width: 20%;">')
            print("********************")
            print(html_content_with_styles)
            return render(request, "result.html", context={"result": html_content_with_styles})
        else:
            print(form_test.errors)
            return redirect('index')
    else:
        return redirect('index')




def generate_prompt(description, name, skill, weekly, other, deadline):
    return f"""tu es un projet manager/planner.
ton but est d'aider les gens a mener a bien leur projet pour cela tu vas leurs donner le plus d'information complementaire possible. Tu vas a partir d'une description de projet de donner un plan
detailler des etapes a passe la roadmap doit contenir toutes les taches, cela doit etre extremement bien detailler et precis. Ainsi qu'un planning et une
distribution des roles. Ne fait aucune phrase pour introduire la reponse. Renvoie une roadmap detaillant precisement le chemin a suivre, et ensuite renvoie le planning sous forme de tableau/calendrier si le delai n'est pas suffisant mets une phrase pour l'expliquer et propose quand meme le planning.
n'oublie pas de mettre en tout premier une table des matieres pour presenter l'aide que tu vas fournir.
Renvoie tout sous forme de MARKDOWN, soit le plus propre possible et mets un titre avec le nom du projet. le Titre doit etre la PREMIERE chose que tu ecris, RIEN n'est avant. inclue un chapitre Prérequis technique. Ajoute une section conseil
qui sont des conseils pratique a suivre et des ressources a lire ou voir (ne mets pas de lien) afin de se cultiver sur le sujet.

Voici la description du projet : {description}.
Voici la description des personnes disponible pour ce projet : {name, skill, weekly},
et voici la deadline a laquelle doit etre rendu le projet : {deadline}, et enfin voici des informations suplementaires : {other}"""