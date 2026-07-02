import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { Clock, Globe, Mail, MapPin, MessageSquare, Send, User, type LucideIcon } from "lucide-react";
import { Button } from "../components/Button";
import { CONTACT_EMAIL, SITE_NAME } from "../lib/branding";
import { cn } from "../lib/cn";

const fieldClass =
  "w-full rounded-lg border border-neutral-200 bg-white py-3 text-[0.9375rem] text-neutral-900 placeholder:text-neutral-400 transition-all duration-200 focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/25";

const contactInfo: { title: string; text: string; sub?: string; Icon: LucideIcon }[] = [
  {
    title: "E-mail",
    text: CONTACT_EMAIL,
    sub: "Pour les demandes liées à votre compte, précisez l'adresse utilisée à l'inscription.",
    Icon: Mail,
  },
  {
    title: "Zone couverte",
    text: "Afrique de l'Ouest",
    sub: "Bénin, Sénégal, Togo, Côte d'Ivoire et autres marchés publics régionaux.",
    Icon: MapPin,
  },
  {
    title: "Délai de réponse",
    text: "Sous 48 h ouvrées",
    sub: "Du lundi au vendredi, hors jours fériés.",
    Icon: Clock,
  },
];

function FieldIcon({ Icon, className }: { Icon: LucideIcon; className?: string }) {
  return (
    <Icon
      className={cn("pointer-events-none absolute left-3.5 size-4 text-neutral-400", className)}
      strokeWidth={2}
      aria-hidden="true"
    />
  );
}

export function ContactPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const body = [`Nom : ${name}`, `E-mail : ${email}`, "", message].join("\n");
    const mailto = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(
      subject || `Contact ${SITE_NAME}`
    )}&body=${encodeURIComponent(body)}`;
    window.location.href = mailto;
    setSent(true);
  };

  return (
    <div className="bg-gradient-to-b from-white via-surface to-brand-muted/40">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
        <header className="mb-12 text-center">
          <p className="mb-4 inline-flex rounded-full border border-brand/25 bg-brand/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-brand">
            Nous contacter
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-neutral-900 sm:text-4xl lg:text-[2.5rem] lg:leading-tight">
            Contact
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-neutral-600">
            Une question sur {SITE_NAME} ? Écrivez-nous, nous vous répondrons dans les meilleurs
            délais.
          </p>
        </header>

        <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(280px,340px)]">
          {/* Formulaire */}
          <div className="rounded-2xl border border-neutral-100 bg-white p-6 shadow-xl sm:p-8">
            <div className="mb-6 flex gap-3 rounded-xl border border-brand-200 bg-brand-50 px-4 py-3.5 text-sm text-neutral-700">
              <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-brand/15">
                <Mail className="size-4 text-brand" strokeWidth={2} aria-hidden="true" />
              </div>
              <div className="min-w-0">
                <p>
                  <span className="font-medium">E-mail :</span>{" "}
                  <a href={`mailto:${CONTACT_EMAIL}`} className="text-brand hover:underline">
                    {CONTACT_EMAIL}
                  </a>
                </p>
                <p className="mt-1 text-neutral-500">
                  Pour les demandes liées à votre compte, précisez l&apos;adresse e-mail utilisée
                  à l&apos;inscription.
                </p>
              </div>
            </div>

            {sent ? (
              <div className="rounded-xl border border-brand-200 bg-brand-50 px-4 py-6 text-center text-sm text-brand-800">
                <p className="font-medium">Votre client mail devrait s&apos;ouvrir.</p>
                <p className="mt-2">
                  Si rien ne se passe, envoyez directement un e-mail à{" "}
                  <a href={`mailto:${CONTACT_EMAIL}`} className="underline">
                    {CONTACT_EMAIL}
                  </a>
                  .
                </p>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => setSent(false)}
                >
                  Envoyer un autre message
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="contact-name" className="mb-1.5 block text-sm font-medium text-neutral-700">
                    Nom
                  </label>
                  <div className="relative">
                    <FieldIcon Icon={User} className="top-1/2 -translate-y-1/2" />
                    <input
                      id="contact-name"
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className={cn(fieldClass, "pl-10")}
                      placeholder="Votre nom"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="contact-email" className="mb-1.5 block text-sm font-medium text-neutral-700">
                    E-mail
                  </label>
                  <div className="relative">
                    <FieldIcon Icon={Mail} className="top-1/2 -translate-y-1/2" />
                    <input
                      id="contact-email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className={cn(fieldClass, "pl-10")}
                      placeholder="votre@email.com"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="contact-subject" className="mb-1.5 block text-sm font-medium text-neutral-700">
                    Objet
                  </label>
                  <div className="relative">
                    <FieldIcon Icon={MessageSquare} className="top-1/2 -translate-y-1/2" />
                    <input
                      id="contact-subject"
                      type="text"
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                      className={cn(fieldClass, "pl-10")}
                      placeholder="Objet de votre message"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="contact-message" className="mb-1.5 block text-sm font-medium text-neutral-700">
                    Message
                  </label>
                  <div className="relative">
                    <FieldIcon Icon={MessageSquare} className="top-3.5" />
                    <textarea
                      id="contact-message"
                      required
                      rows={5}
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      className={cn(fieldClass, "resize-y pl-10")}
                      placeholder="Votre message…"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  className="group inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-brand px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-brand/20 transition-all duration-200 hover:scale-[1.02] hover:bg-brand-dark hover:shadow-xl hover:shadow-brand/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2"
                >
                  Envoyer le message
                  <Send
                    className="size-4 transition-transform group-hover:translate-x-0.5"
                    strokeWidth={2}
                    aria-hidden="true"
                  />
                </button>
              </form>
            )}
          </div>

          {/* Informations latérales */}
          <aside className="space-y-4">
            <div className="rounded-2xl border border-neutral-100 bg-white p-6 shadow-card">
              <div className="mb-5 flex items-center gap-2">
                <div className="flex size-9 items-center justify-center rounded-full bg-brand-muted">
                  <Globe className="size-4 text-brand" strokeWidth={2} aria-hidden="true" />
                </div>
                <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-900">
                  Nos coordonnées
                </h2>
              </div>

              <ul className="space-y-5">
                {contactInfo.map(({ title, text, sub, Icon }) => (
                  <li key={title} className="flex gap-3">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-brand-muted transition-colors">
                      <Icon className="size-5 text-brand" strokeWidth={2} aria-hidden="true" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-semibold uppercase tracking-wide text-brand">
                        {title}
                      </p>
                      {title === "E-mail" ? (
                        <a
                          href={`mailto:${CONTACT_EMAIL}`}
                          className="mt-0.5 block text-sm font-medium text-neutral-800 break-all hover:text-brand hover:underline"
                        >
                          {text}
                        </a>
                      ) : (
                        <p className="mt-0.5 text-sm font-medium text-neutral-800">{text}</p>
                      )}
                      {sub && <p className="mt-1 text-xs leading-relaxed text-neutral-500">{sub}</p>}
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            <p className="rounded-xl border border-brand/15 bg-brand/5 px-4 py-3 text-center text-xs leading-relaxed text-neutral-600">
              Vous préférez nous écrire directement ? Cliquez sur l&apos;adresse e-mail ci-dessus ou
              utilisez le formulaire.
            </p>
          </aside>
        </div>

        <p className="mt-10 text-center text-sm text-neutral-500">
          Consultez aussi nos{" "}
          <Link to="/conditions-utilisation" className="text-brand hover:underline">
            conditions d&apos;utilisation
          </Link>
          .
        </p>
      </div>
    </div>
  );
}
