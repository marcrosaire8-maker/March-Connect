import {
  BookOpen,
  Briefcase,
  Building2,
  Droplets,
  Laptop,
  Package,
  Stethoscope,
  Tractor,
  Truck,
  Zap,
  type LucideIcon,
} from "lucide-react";

const SECTEUR_ICON_RULES: { pattern: RegExp; Icon: LucideIcon }[] = [
  { pattern: /eau|assainissement|potable/i, Icon: Droplets },
  { pattern: /btp|travaux|construction|bâtiment|batiment/i, Icon: Building2 },
  { pattern: /informatique|télécom|telecom|numérique|numerique/i, Icon: Laptop },
  { pattern: /santé|sante|médical|medical/i, Icon: Stethoscope },
  { pattern: /transport|logistique/i, Icon: Truck },
  { pattern: /énergie|energie|électr/i, Icon: Zap },
  { pattern: /agriculture|agro/i, Icon: Tractor },
  { pattern: /fourniture|équipement|equipement/i, Icon: Package },
  { pattern: /étude|etude|conseil/i, Icon: BookOpen },
];

export function getSecteurIcon(nom?: string | null): LucideIcon {
  if (!nom) return Briefcase;
  for (const rule of SECTEUR_ICON_RULES) {
    if (rule.pattern.test(nom)) return rule.Icon;
  }
  return Briefcase;
}
