import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { IdleTimeoutProvider } from "@/providers/IdleTimeoutProvider";
import { RecordingStateProvider } from "@/providers/RecordingStateProvider";
import Index from "./pages/Index";
import { VoiceProfile } from "./pages/VoiceProfile";
import Auth from "./pages/Auth";
import AcceptInvitation from "./pages/AcceptInvitation";
import SecuritySettings from "./pages/SecuritySettings";
import { CallsSearch } from "./pages/CallsSearch";
import { CallAnalysisPage } from "./pages/CallAnalysis";
import Appointments from "./pages/Appointments";
import ContactPreferences from "./pages/ContactPreferences";
import EnterpriseReports from "./pages/EnterpriseReports";
import Leaderboard from "./pages/Leaderboard";
import { SystemAdmin } from "./pages/SystemAdmin";
import SystemCheck from "./pages/SystemCheck";
import { PatientDetails } from "./pages/PatientDetails";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <RecordingStateProvider>
          <IdleTimeoutProvider>
            <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/appointments" element={<Appointments />} />
            <Route path="/voice-profile" element={<VoiceProfile />} />
            <Route path="/search" element={<CallsSearch />} />
            <Route path="/contact-preferences" element={<ContactPreferences />} />
            <Route path="/enterprise-reports" element={<EnterpriseReports />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="/system-admin" element={<SystemAdmin />} />
            <Route path="/system-check" element={<SystemCheck />} />
            <Route path="/patient/:patientName" element={<PatientDetails />} />
            <Route path="/analysis/:callId" element={<CallAnalysisPage />} />
            <Route path="/auth" element={<Auth />} />
            <Route path="/accept-invitation" element={<AcceptInvitation />} />
            <Route path="/security-settings" element={<SecuritySettings />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
            </Routes>
          </IdleTimeoutProvider>
        </RecordingStateProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
