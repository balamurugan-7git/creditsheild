// ============================================================
// CrediShield AI – TypeScript Types & Interfaces
// Mirrors backend Pydantic schemas
// ============================================================

/** Possible user roles in the system */
export type UserRole = 'applicant' | 'loan_officer';

/** Authenticated user object */
export interface User {
  id: number;
  email: string;
  role: UserRole;
  full_name: string | null;
  created_at: string;
}

/** JWT token response from /api/auth/token */
export interface AuthTokens {
  access_token: string;
  token_type: string;
}

/** A single SHAP feature contribution factor */
export interface ShapFactor {
  feature: string;
  shap_value: number;
  direction: 'increases_risk' | 'decreases_risk';
  display_name: string;
}

/** The three possible AI decisions */
export type DecisionType = 'approved' | 'manual_review' | 'rejected';

/** Full loan application record returned by the API */
export interface Application {
  id: number;
  applicant_id: number;
  probability: number;
  decision: DecisionType;
  model_version: string;
  shap_top_factors: ShapFactor[];
  officer_override: DecisionType | null;
  override_reason: string | null;
  override_by: number | null;
  override_at: string | null;
  scored_at: string;
  input_features: Record<string, unknown>;
}

/** Paginated list of applications */
export interface ApplicationListResponse {
  applications: Application[];
  total: number;
}

/** Input payload for submitting a new loan application */
export interface LoanApplicationInput {
  CODE_GENDER: 'M' | 'F' | 'XNA';
  FLAG_OWN_CAR: 'Y' | 'N';
  FLAG_OWN_REALTY: 'Y' | 'N';
  CNT_CHILDREN: number;
  AMT_INCOME_TOTAL: number;
  AMT_CREDIT: number;
  AMT_ANNUITY?: number;
  AMT_GOODS_PRICE?: number;
  NAME_INCOME_TYPE: string;
  NAME_EDUCATION_TYPE: string;
  NAME_FAMILY_STATUS: string;
  NAME_HOUSING_TYPE: string;
  DAYS_BIRTH: number;
  DAYS_EMPLOYED: number;
  DAYS_REGISTRATION: number;
  DAYS_ID_PUBLISH: number;
  NAME_CONTRACT_TYPE: string;
  EXT_SOURCE_1?: number;
  EXT_SOURCE_2?: number;
  EXT_SOURCE_3?: number;
  ORGANIZATION_TYPE?: string;
  OCCUPATION_TYPE?: string;
  REGION_RATING_CLIENT?: number;
  OWN_CAR_AGE?: number;
  CNT_FAM_MEMBERS?: number;
}

/** Loan officer override request payload */
export interface OverrideRequest {
  decision: 'approved' | 'rejected';
  reason: string;
}
