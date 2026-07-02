import { Link } from "react-router-dom";
import { LegalDocumentLayout, LegalSection } from "../components/legal/LegalDocumentLayout";
import { SITE_NAME } from "../lib/branding";

export function PolitiqueConfidentialitePage() {
  return (
    <LegalDocumentLayout badge="Confidentialité" title="Politique de confidentialité">
      <LegalSection title="1. Responsable du traitement">
        <p>
          Le responsable du traitement des données personnelles collectées via {SITE_NAME} est
          l&apos;exploitant de la plateforme, joignable via la page{" "}
          <Link to="/contact" className="text-brand hover:underline">
            Contact
          </Link>
          .
        </p>
      </LegalSection>

      <LegalSection title="2. Données collectées">
        <p>Nous collectons les données suivantes :</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>Adresse e-mail et mot de passe (inscription)</li>
          <li>Prénom et nom (optionnels)</li>
          <li>Identifiant OAuth (Google, Apple) si connexion sociale</li>
          <li>Préférences d&apos;alertes : secteurs, pays, mots-clés</li>
          <li>Historique de navigation sur la plateforme (favoris, sites suivis)</li>
          <li>Logs techniques : dates de connexion, adresse IP (sécurité)</li>
        </ul>
      </LegalSection>

      <LegalSection title="3. Finalités du traitement">
        <p>Les données sont utilisées pour :</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>Créer et gérer votre compte utilisateur</li>
          <li>Envoyer les e-mails transactionnels (bienvenue, réinitialisation mot de passe)</li>
          <li>Envoyer les alertes personnalisées sur les appels d&apos;offres</li>
          <li>Améliorer le service et assurer la sécurité de la plateforme</li>
        </ul>
      </LegalSection>

      <LegalSection title="4. Base légale">
        <p>
          Le traitement repose sur l&apos;exécution du contrat (utilisation du service), votre
          consentement (inscription et acceptation des conditions) et l&apos;intérêt légitime
          (sécurité, amélioration du service).
        </p>
      </LegalSection>

      <LegalSection title="5. Durée de conservation">
        <p>
          Les données sont conservées tant que votre compte est actif. Après suppression du compte,
          les données personnelles sont effacées dans un délai raisonnable, sauf obligation légale
          de conservation (logs de sécurité).
        </p>
      </LegalSection>

      <LegalSection title="6. Destinataires des données">
        <p>Les données peuvent être traitées par nos sous-traitants techniques :</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>Hébergeur (Render) — serveurs API et site web</li>
          <li>MongoDB Atlas — base de données</li>
          <li>Brevo (ou SMTP) — envoi des e-mails</li>
          <li>Google / Apple — authentification OAuth (si utilisée)</li>
        </ul>
        <p>Aucune donnée n&apos;est vendue à des tiers à des fins commerciales.</p>
      </LegalSection>

      <LegalSection title="7. Vos droits">
        <p>Vous disposez des droits suivants :</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>Accès à vos données personnelles</li>
          <li>Rectification des informations inexactes</li>
          <li>Suppression de votre compte (depuis Mon compte)</li>
          <li>Opposition ou limitation du traitement</li>
          <li>Désabonnement des alertes e-mail</li>
        </ul>
        <p>
          Pour exercer vos droits, contactez-nous via la page{" "}
          <Link to="/contact" className="text-brand hover:underline">
            Contact
          </Link>{" "}
          ou utilisez la page{" "}
          <Link to="/desabonnement" className="text-brand hover:underline">
            Désabonnement
          </Link>
          .
        </p>
      </LegalSection>

      <LegalSection title="8. Cookies et stockage local">
        <p>
          Le site utilise un jeton d&apos;authentification stocké en session navigateur
          (sessionStorage) pour maintenir votre connexion. Aucun cookie publicitaire n&apos;est
          utilisé.
        </p>
      </LegalSection>

      <LegalSection title="9. Sécurité">
        <p>
          Nous mettons en œuvre des mesures techniques (chiffrement HTTPS, mots de passe hashés,
          rate limiting) pour protéger vos données. Aucun système n&apos;étant infaillible, nous
          vous encouragez à utiliser un mot de passe fort et unique.
        </p>
      </LegalSection>

      <LegalSection title="10. Modifications">
        <p>
          Cette politique peut être mise à jour. La date de dernière révision est indiquée en haut
          de page. Nous vous informerons des changements significatifs si nécessaire.
        </p>
      </LegalSection>
    </LegalDocumentLayout>
  );
}
