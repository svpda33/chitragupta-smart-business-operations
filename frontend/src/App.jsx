import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { useAuth } from "./context/AuthContext.jsx";
import AppLayout from "./layouts/AppLayout.jsx";
import LandingPage from "./pages/LandingPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import SignupPage from "./pages/SignupPage.jsx";
import OnboardingPage from "./pages/OnboardingPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import CataloguePage from "./pages/CataloguePage.jsx";
import InventoryPage from "./pages/InventoryPage.jsx";
import NotepadPage from "./pages/NotepadPage.jsx";
import CustomersPage from "./pages/CustomersPage.jsx";
import CustomerDetailPage from "./pages/CustomerDetailPage.jsx";
import CustomerFormPage from "./pages/CustomerFormPage.jsx";
import InvoicesPage from "./pages/InvoicesPage.jsx";
import InvoiceDetailPage from "./pages/InvoiceDetailPage.jsx";
import InvoiceFormPage from "./pages/InvoiceFormPage.jsx";
import PaymentsPage from "./pages/PaymentsPage.jsx";
import PaymentFormPage from "./pages/PaymentFormPage.jsx";
import CashFlowPage from "./pages/CashFlowPage.jsx";
import RemindersPage from "./pages/RemindersPage.jsx";
import AiAssistantPage from "./pages/AiAssistantPage.jsx";
import SettingsPage from "./pages/SettingsPage.jsx";
import NotFoundPage from "./pages/NotFoundPage.jsx";

function ProtectedWorkspace() {
  const { isAuthenticated, onboardingCompleted, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-[#0b1120]">
        <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!onboardingCompleted) {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}

export default function App() {
  return (
    <Routes>
      {/* Public SaaS Landing & Auth */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/onboarding" element={<OnboardingPage />} />

      {/* Authenticated Business Workspace */}
      <Route element={<ProtectedWorkspace />}>
        <Route element={<AppLayout />}>
          <Route path="dashboard" element={<DashboardPage />} />

          {/* Catalogue & Inventory */}
          <Route path="catalogue" element={<CataloguePage />} />
          <Route path="inventory" element={<InventoryPage />} />

          {/* Customers */}
          <Route path="customers" element={<CustomersPage />} />
          <Route path="customers/new" element={<CustomerFormPage />} />
          <Route path="customers/:id" element={<CustomerDetailPage />} />
          <Route path="customers/:id/edit" element={<CustomerFormPage />} />

          {/* Invoices */}
          <Route path="invoices" element={<InvoicesPage />} />
          <Route path="invoices/new" element={<InvoiceFormPage />} />
          <Route path="invoices/:id" element={<InvoiceDetailPage />} />
          <Route path="invoices/:id/edit" element={<InvoiceFormPage />} />

          {/* Payments */}
          <Route path="payments" element={<PaymentsPage />} />
          <Route path="payments/new" element={<PaymentFormPage />} />

          {/* Financial Intelligence & Workspace */}
          <Route path="cash-flow" element={<CashFlowPage />} />
          <Route path="reminders" element={<RemindersPage />} />
          <Route path="notepad" element={<NotepadPage />} />
          <Route path="ai-assistant" element={<AiAssistantPage />} />
          <Route path="settings" element={<SettingsPage />} />

          {/* Catch-all */}
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
