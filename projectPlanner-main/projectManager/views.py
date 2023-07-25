from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import FormView
from django.contrib.auth.models import User
from requests import request
import sesame.utils
from .forms import EmailLoginForm

class EmailLoginView(FormView):
    template_name = "projectManager/email_login.html"
    form_class = EmailLoginForm

    def get_user(self, email):
        """Find the user with this email address."""
        User = get_user_model()
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    def create_link(self, user):
        """Create a login link for this user."""
        link = reverse("login")
        link = self.request.build_absolute_uri(link)
        link += sesame.utils.get_query_string(user)
        return link

    def send_email(self, user, link):
        """Send an email with this login link to this user."""
        user.email_user(
            subject="[django-sesame] Log in to our app",
            message=f"""\
Hello,

You requested that we send you a link to log in to our app:

    {link}

Thank you for using django-sesame!
""",
        )

    def create_user_and_send_token(self, email):
        # Créer un nouvel utilisateur avec le nom d'utilisateur et l'adresse e-mail spécifiés
        user = User.objects.create_user(email=email, username=email)
        # Générer un token pour l'utilisateur
        token = sesame.utils.get_query_string(user)
        # Générer un lien contenant le token
        link = request.build_absolute_uri(reverse('sesame-login') + token)
        # Envoyer le lien d'accès unique à l'utilisateur par e-mail
        user.email_user(
            subject='Votre lien d\'accès unique',
            message=f'Voici votre lien d\'accès unique : {link}',
        )

    def email_submitted(self, email):
        user = self.get_user(email)
        if user is None:
            # Ignore the case when no user is registered with this address.
            # Possible improvement: send an email telling them to register.
            print("user not found:", email)
            self.create_user_and_send_token(email)
            return
        link = self.create_link(user)
        self.send_email(user, link)

    def form_valid(self, form):
        self.email_submitted(form.cleaned_data["email"])
        return render(self.request, "projectManager/email_login_success.html")

def index(request):
    return render(request, 'projectManager/index.html', context={})



# """tu es un projet manager/planner
# ton but est d'aider les gens a mener a bien leur projet pour cela tu vas leurs donner le plus d'information complementaire possible. Tu vas a partir d'une description de projet de donner un plan
# detailler des etapes a passe la roadmap doit contenir toutes les taches, cela doit etre extremement bien detailler et precis. Ainsi qu'un planning et une
# distribution des roles. Ne fait aucune phrase pour introduire la reponse. Renvoie une roadmap detaillant precisement le chemin a suivre, et ensuite renvoie le planning sous forme de tableau/calendrier si le delai n'est pas suffisant mets une phrase pour l'expliquer et propose quand meme le planning.
# n'oublie pas de mettre en tout premier une table des matieres pour presenter l'aide que tu vas fournir.
# Renvoie le tout sous forme de markdown. inclue un chapitre Prérequis technique. Ajoute une section conseil
# qui sont des conseils pratique a suivre et des ressources a lire ou voir (ne mets pas de lien) afin de se cultiver sur le sujet.

# Voici la description du projet {Le projet consiste à construire un moteur de recherche en Java, utilisable en ligne de commande.

# Celui-ci permettra d'effectuer une recherche par mots-clés sur un ensemble de pages web préalablement indexées.}.
# Voici la description des personnes disponible pour ce projet {thomas, developpeur, 35 heures par semaines},
# et voici la deadline a laquelle doit etre rendu le projet {le projet doit etre rendu dans une semaine}"""