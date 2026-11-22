import { lazy, Suspense } from "react";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { useAuth } from "./context/AuthContext.jsx";
import AppLayout from "./layouts/AppLayout.jsx";
const LandingPage = lazy(() => import("./pages/LandingPage.jsx"));
const LoginPage = lazy(() => import("./pages/LoginPage.jsx"));
const SignupPage = lazy(() => import("./pages/SignupPage.jsx"));
const OnboardingPage = lazy(() => import("./pages/OnboardingPage.jsx"));
const DashboardPage = lazy(() => import("./pages/DashboardPage.jsx"));
const CataloguePage = lazy(() => import("./pages/CataloguePage.jsx"));
const InventoryPage = lazy(() => import("./pages/InventoryPage.jsx"));
const NotepadPage = lazy(() => import("./pages/NotepadPage.jsx"));
const CustomersPage = lazy(() => import("./pages/CustomersPage.jsx"));
const CustomerDetailPage = lazy(() => import("./pages/CustomerDetailPage.jsx"));
const CustomerFormPage = lazy(() => import("./pages/CustomerFormPage.jsx"));
const InvoicesPage = lazy(() => import("./pages/InvoicesPage.jsx"));
const InvoiceDetailPage = lazy(() => import("./pages/InvoiceDetailPage.jsx"));
const InvoiceFormPage = lazy(() => import("./pages/InvoiceFormPage.jsx"));
const PaymentsPage = lazy(() => import("./pages/PaymentsPage.jsx"));
const PaymentFormPage = lazy(() => import("./pages/PaymentFormPage.jsx"));
const CashFlowPage = lazy(() => import("./pages/CashFlowPage.jsx"));
const RemindersPage = lazy(() => import("./pages/RemindersPage.jsx"));
const AiAssistantPage = lazy(() => import("./pages/AiAssistantPage.jsx"));
const SettingsPage = lazy(() => import("./pages/SettingsPage.jsx"));
const NotFoundPage = lazy(() => import("./pages/NotFoundPage.jsx"));

function PageLoader() {
  return (
    <div className="min-h-[50vh] flex items-center justify-center">
      <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
    </div>
  );
}

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
    <Suspense fallback={<PageLoader />}>
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
    </Suspense>
  );
}
