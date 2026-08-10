import { Badge, type BadgeProps } from "@yenimenzil/ui";

interface PropertyBadgeProps extends BadgeProps {
  kind: "premium" | "new" | "price_drop" | "verified" | "promoted";
  label?: string;
}

export function PropertyBadge({ kind, label, ...props }: PropertyBadgeProps) {
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
          {label ?? "Yeni"}
        </Badge>
      );
    case "price_drop":
      return (
        <Badge variant="green" {...props}>
          {label ?? "Qiymət düşüb"}
        </Badge>
      );
    case "verified":
      return (
        <Badge variant="neutral" {...props}>
          {label ?? "Təsdiqlənib"}
        </Badge>
      );
    case "promoted":
      return (
        <Badge variant="amber" {...props}>
          {label ?? "Önə çıxarılıb"}
        </Badge>
      );
  }
}
