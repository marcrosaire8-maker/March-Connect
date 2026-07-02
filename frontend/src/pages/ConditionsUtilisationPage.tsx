import { Link } from "react-router-dom";
import { LegalDocumentLayout, LegalSection } from "../components/legal/LegalDocumentLayout";
import { SITE_NAME } from "../lib/branding";

export function ConditionsUtilisationPage() {
  return (
    <LegalDocumentLayout
      badge="Conditions d'utilisation"
      title="Conditions d'utilisation"
      backTo={{ label: "Retour à l'inscription", href: "/inscription" }}
    >
      <LegalSection title="1. Objet">
        <p>
          Les présentes conditions régissent l&apos;accès et l&apos;utilisation de la plateforme{" "}
          {SITE_NAME}, service de veille sur les appels d&apos;offres en Afrique de l&apos;Ouest.
          En créant un compte ou en utilisant le site, vous acceptez ces conditions dans leur intégralité.
        </p>
      </LegalSection>

      <LegalSection title="2. Description du service">
        <p>
          {SITE_NAME} agrège et présente des appels d&apos;offres issus de sources publiques officielles.
          Le service permet de consulter les offres, de configurer des alertes par e-mail selon vos secteurs
          et pays d&apos;intérêt, et de gérer un espace personnel.
        </p>
        <p>
          Les informations publiées sont fournies à titre indicatif. L&apos;exploitant s&apos;efforce d&apos;assurer
          leur exactitude mais ne garantit pas l&apos;exhaustivité ni l&apos;absence d&apos;erreur. L&apos;utilisateur
          doit toujours vérifier les détails auprès de la source officielle avant toute candidature.
        </p>
      </LegalSection>

      <LegalSection title="3. Inscription et compte utilisateur">
        <p>
          L&apos;inscription nécessite une adresse e-mail valide et un mot de passe respectant les critères
          de sécurité affichés sur le formulaire. Vous êtes responsable de la confidentialité de vos identifiants
          et de toute activité réalisée depuis votre compte.
        </p>
        <p>
          Vous vous engagez à fournir des informations exactes et à mettre à jour vos coordonnées si nécessaire.
          Un compte ne peut être utilisé que par une seule personne physique ou morale titulaire.
        </p>
      </LegalSection>

      <LegalSection title="4. Alertes et communications">
        <p>
          En vous inscrivant, vous pouvez recevoir des e-mails transactionnels (bienvenue, réinitialisation
          de mot de passe) et des alertes personnalisées sur les offres correspondant à vos préférences.
        </p>
        <p>
          Vous pouvez modifier vos préférences d&apos;alerte depuis votre espace « Mon compte » ou vous
          désinscrire via la page{" "}
          <Link to="/desabonnement" className="text-brand hover:underline">
            Désabonnement
          </Link>
          .
        </p>
      </LegalSection>

      <LegalSection title="5. Utilisation acceptable">
        <p>L&apos;utilisateur s&apos;engage à ne pas :</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>utiliser le service à des fins illégales ou frauduleuses ;</li>
          <li>tenter d&apos;accéder de manière non autorisée aux systèmes ou données ;</li>
          <li>extraire massivement les données (scraping automatisé non autorisé) ;</li>
          <li>publier ou transmettre des contenus nuisibles, diffamatoires ou contraires à la loi ;</li>
          <li>usurper l&apos;identité d&apos;un tiers ou créer de faux comptes.</li>
        </ul>
      </LegalSection>

      <LegalSection title="6. Propriété intellectuelle">
        <p>
          La marque, l&apos;interface, le code et les éléments graphiques de {SITE_NAME} sont protégés.
          Les contenus des appels d&apos;offres restent la propriété de leurs émetteurs respectifs (organismes
          publics, plateformes officielles).
        </p>
      </LegalSection>

      <LegalSection title="7. Disponibilité et responsabilité">
        <p>
          Le service est fourni « en l&apos;état ». L&apos;exploitant ne saurait être tenu responsable des
          décisions prises sur la base des informations affichées, des retards de notification, des
          interruptions de service ou des erreurs provenant des sources tierces.
        </p>
      </LegalSection>

      <LegalSection title="8. Suspension et résiliation">
        <p>
          L&apos;exploitant se réserve le droit de suspendre ou supprimer un compte en cas de violation
          des présentes conditions. Vous pouvez supprimer votre compte à tout moment depuis « Mon compte ».
        </p>
      </LegalSection>

      <LegalSection title="9. Données personnelles">
        <p>
          Le traitement de vos données est décrit dans notre{" "}
          <Link to="/politique-de-confidentialite" className="text-brand hover:underline">
            Politique de confidentialité
          </Link>
          .
        </p>
      </LegalSection>

      <LegalSection title="10. Droit applicable">
        <p>
          Les présentes conditions sont régies par le droit applicable dans le pays d&apos;exploitation
          du service. En cas de litige, les parties s&apos;efforceront de trouver une solution amiable
          avant toute action judiciaire.
        </p>
      </LegalSection>
    </LegalDocumentLayout>
  );
}
