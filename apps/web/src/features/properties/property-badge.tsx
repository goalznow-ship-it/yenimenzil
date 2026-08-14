import { Badge, type BadgeProps } from "@yenimenzil/ui";
import { useI18n } from "@/components/i18n-provider";

interface PropertyBadgeProps extends BadgeProps {
  kind: "premium" | "new" | "price_drop" | "verified" | "promoted";
  label?: string;
}

export function PropertyBadge({ kind, label, ...props }: PropertyBadgeProps) {
  const { t } = useI18n();
  switch (kind) {
    case "premium":
      return (
        <Badge variant="gold" {...props}>
          {label ?? "Premium"}
        </Badge>
      );
    case "new":
      return (
        <Badge variant="brand" {...props}>
          {label ?? t("listing.new")}
        </Badge>
      );
    case "price_drop":
      return (
        <Badge variant="green" {...props}>
          {label ?? t("listing.priceDrop")}
        </Badge>
      );
    case "verified":
      return (
        <Badge variant="neutral" {...props}>
          {label ?? t("listing.verified")}
        </Badge>
      );
    case "promoted":
      return (
        <Badge variant="amber" {...props}>
          {label ?? t("listing.promoted")}
        </Badge>
      );
  }
}
