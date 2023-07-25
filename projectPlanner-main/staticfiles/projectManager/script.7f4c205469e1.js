function addPerson() {
  const template = document.querySelector('[data-template-manager-target="container"] [data-controller="visibility"]');
  const clone = template.cloneNode(true);
  document.getElementById('characters').appendChild(clone);
}

function removePersonTemplate(event) {
  event.target.closest('.grid').remove();
}
