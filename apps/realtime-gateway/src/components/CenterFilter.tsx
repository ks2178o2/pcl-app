import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useOrganizationData } from '@/hooks/useOrganizationData';
import { MapPin } from 'lucide-react';
interface CenterFilterProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}
export const CenterFilter: React.FC<CenterFilterProps> = ({
  value,
  onChange,
  placeholder = "All Centers",
  className
}) => {
  const {
    centers,
    loading
  } = useOrganizationData();
  if (loading) {
    return <div className="space-y-2">
        <label className="text-sm font-medium flex items-center gap-2">
          <MapPin className="h-4 w-4" />
          Center
        </label>
        <div className="h-10 bg-muted rounded-md animate-pulse" />
      </div>;
  }
  return <div className="space-y-2">
      <label className="text-sm font-medium flex items-center gap-2 my-[8px] py-[4px]">
        <MapPin className="h-4 w-4" />
        Center
      </label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className={className}>
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Centers</SelectItem>
          {centers.map(center => <SelectItem key={center.id} value={center.id}>
              {center.name} - {center.region?.name}
            </SelectItem>)}
        </SelectContent>
      </Select>
    </div>;
};