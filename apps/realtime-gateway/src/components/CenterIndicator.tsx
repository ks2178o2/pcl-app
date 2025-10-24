import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { MapPin, ChevronDown } from 'lucide-react';
import { useCenterSession } from '@/hooks/useCenterSession';

export const CenterIndicator = () => {
  const { activeCenter, availableCenters, getActiveCenterInfo, setActiveCenter } = useCenterSession();
  
  const activeCenterInfo = getActiveCenterInfo();
  
  if (!activeCenterInfo) return null;

  const canSwitchCenters = availableCenters.length > 1;

  if (!canSwitchCenters) {
    return (
      <Badge variant="secondary" className="flex items-center gap-2">
        <MapPin className="h-3 w-3" />
        {activeCenterInfo.name}
      </Badge>
    );
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="flex items-center gap-2">
          <MapPin className="h-3 w-3" />
          {activeCenterInfo.name}
          <ChevronDown className="h-3 w-3" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-56" align="end">
        <div className="space-y-2">
          <div className="text-sm font-medium text-muted-foreground">Switch Center</div>
          {availableCenters.map((center) => (
            <Button
              key={center.id}
              variant={center.id === activeCenter ? "default" : "ghost"}
              size="sm"
              className="w-full justify-start"
              onClick={() => setActiveCenter(center.id)}
            >
              <MapPin className="h-3 w-3 mr-2" />
              <div className="text-left">
                <div className="text-sm">{center.name}</div>
                {center.region && (
                  <div className="text-xs text-muted-foreground">{center.region.name}</div>
                )}
              </div>
            </Button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
};