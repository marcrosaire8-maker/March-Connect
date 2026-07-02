import { Link } from "react-router-dom";
import { LegalDocumentLayout, LegalSection } from "../components/legal/LegalDocumentLayout";
import { CONTACT_EMAIL, SITE_NAME } from "../lib/branding";

export function MentionsLegalesPage() {
  return (
    <LegalDocumentLayout badge="Mentions légales" title="Mentions légales">
      <LegalSection title="1. Éditeur du site">
        <p>
          <strong>{SITE_NAME}</strong>
          <br />
          Plateforme de veille sur les appels d&apos;offres en Afrique de l&apos;Ouest.
        </p>
        <p>
          Contact :{" "}
          <a href={`mailto:${CONTACT_EMAIL}`} className="text-brand hover:underline">
            {CONTACT_EMAIL}
          </a>{" "}
          —{" "}
          <Link to="/contact" className="text-brand hover:underline">
            Formulaire de contact
          </Link>
        </p>
        <p className="text-neutral-500">
          Les coordonnées complètes de l&apos;éditeur (raison sociale, adresse, numéro
          d&apos;immatriculation) doivent être renseignées par le propriétaire du site lors de la
          mise en production.
        </p>
      </LegalSection>

      <LegalSection title="2. Directeur de la publication">
        <p>
          Le directeur de la publication est le représentant légal de l&apos;exploitant de{" "}
          {SITE_NAME}, désigné lors de la mise en service de la plateforme.
        </p>
      </LegalSection>

      <LegalSection title="3. Hébergement">
        <p>
          <strong>Render Services, Inc.</strong>
          <br />
          525 Brannan Street, Suite 300
          <br />
          San Francisco, CA 94107, États-Unis
          <br />
          <a
            href="https://render.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-brand hover:underline"
          >
            https://render.com
          </a>
        </p>
        <p>
          Base de données hébergée par <strong>MongoDB Atlas</strong> (MongoDB, Inc.).
        </p>
      </LegalSection>

      <LegalSection title="4. Propriété intellectuelle">
        <p>
          L&apos;ensemble des éléments composant le site {SITE_NAME} (textes, graphismes, logo,
          logiciels, structure) est protégé par le droit de la propriété intellectuelle.
        </p>
        <p>
          Les contenus des appels d&apos;offres proviennent de sources publiques officielles et
          restent la propriété de leurs émetteurs respectifs.
        </p>
      </LegalSection>

      <LegalSection title="5. Limitation de responsabilité">
        <p>
          {SITE_NAME} s&apos;efforce d&apos;assurer l&apos;exactitude des informations diffusées
          mais ne garantit pas l&apos;exhaustivité ni l&apos;absence d&apos;erreur. L&apos;utilisateur
          doit vérifier toute information auprès de la source officielle avant toute décision.
        </p>
        <p>
          L&apos;éditeur ne saurait être tenu responsable des dommages directs ou indirects résultant
          de l&apos;utilisation du site ou de l&apos;impossibilité d&apos;y accéder.
        </p>
      </LegalSection>

      <LegalSection title="6. Liens hypertextes">
        <p>
          Le site peut contenir des liens vers des sites tiers (portails officiels d&apos;appels
          d&apos;offres). {SITE_NAME} n&apos;exerce aucun contrôle sur ces sites et décline toute
          responsabilité quant à leur contenu.
        </p>
      </LegalSection>

      <LegalSection title="7. Droit applicable">
        <p>
          Les présentes mentions légales sont régies par le droit applicable dans le pays
          d&apos;exploitation du service. Pour toute réclamation, contactez-nous en priorité via la
          page{" "}
          <Link to="/contact" className="text-brand hover:underline">
            Contact
          </Link>
          .
        </p>
      </LegalSection>

      <LegalSection title="8. Documents associés">
        <p>
          <Link to="/conditions-utilisation" className="text-brand hover:underline">
            Conditions d&apos;utilisation
          </Link>
          {" · "}
          <Link to="/politique-de-confidentialite" className="text-brand hover:underline">
            Politique de confidentialité
          </Link>
        </p>
      </LegalSection>
    </LegalDocumentLayout>
  );
}
