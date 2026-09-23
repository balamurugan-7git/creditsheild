// ============================================================
// CrediShield AI – Application Form Component
// Multi-step loan application form with validation
// ============================================================

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, ArrowRight, CheckCircle2, ShieldAlert } from 'lucide-react';
import type { LoanApplicationInput } from '@/types';
import Button from './ui/Button';

// Form validation schema
const formSchema = z.object({
  // Personal
  CODE_GENDER: z.enum(['M', 'F', 'XNA']),
  age_years: z.coerce.number().min(18, 'Must be at least 18').max(90, 'Age must be 90 or below'),
  CNT_CHILDREN: z.coerce.number().min(0, 'Number of children cannot be negative (enter 0 or more)').max(20),
  CNT_FAM_MEMBERS: z.coerce.number().optional().default(1),
  NAME_FAMILY_STATUS: z.string().min(1, 'Required'),
  NAME_EDUCATION_TYPE: z.string().min(1, 'Required'),
  NAME_HOUSING_TYPE: z.string().min(1, 'Required'),

  // Financial
  AMT_INCOME_TOTAL: z.coerce.number().positive('Must be greater than 0'),
  AMT_CREDIT: z.coerce.number().positive('Must be greater than 0'),
  AMT_ANNUITY: z.coerce.number().positive().optional(),
  NAME_INCOME_TYPE: z.string().min(1, 'Required'),
  employment_years: z.coerce.number().min(-1, 'Must be 0 or more (-1 if unemployed)'),
  NAME_CONTRACT_TYPE: z.enum(['Cash loans', 'Revolving loans']),

  // Credit Bureau & Scores
  EXT_SOURCE_1: z.coerce.number().min(0).max(1).optional(),
  EXT_SOURCE_2: z.coerce.number().min(0).max(1).optional(),
  EXT_SOURCE_3: z.coerce.number().min(0).max(1).optional(),

  // Assets & Info
  FLAG_OWN_CAR: z.enum(['Y', 'N']),
  FLAG_OWN_REALTY: z.enum(['Y', 'N']),
  OWN_CAR_AGE: z.coerce.number().min(0).optional(),
  OCCUPATION_TYPE: z.string().optional(),
  ORGANIZATION_TYPE: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

interface ApplicationFormProps {
  onSubmit: (data: LoanApplicationInput) => void;
  isLoading: boolean;
}

export default function ApplicationForm({ onSubmit, isLoading }: ApplicationFormProps) {
  const [step, setStep] = useState(1);

  const {
    register,
    handleSubmit,
    trigger,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      CODE_GENDER: 'M',
      age_years: 32,
      CNT_CHILDREN: 0,
      CNT_FAM_MEMBERS: 2,
      NAME_FAMILY_STATUS: 'Married',
      NAME_EDUCATION_TYPE: 'Higher education',
      NAME_HOUSING_TYPE: 'House / apartment',
      AMT_INCOME_TOTAL: 180000,
      AMT_CREDIT: 450000,
      AMT_ANNUITY: 25000,
      NAME_INCOME_TYPE: 'Working',
      employment_years: 5,
      NAME_CONTRACT_TYPE: 'Cash loans',
      FLAG_OWN_CAR: 'N',
      FLAG_OWN_REALTY: 'Y',
      EXT_SOURCE_2: 0.55,
      EXT_SOURCE_3: 0.60,
      ORGANIZATION_TYPE: 'Business Entity Type 3',
      OCCUPATION_TYPE: 'Laborers',
    },
  });

  const nextStep = async () => {
    let fieldsToValidate: (keyof FormValues)[] = [];
    if (step === 1) {
      fieldsToValidate = ['CODE_GENDER', 'age_years', 'CNT_CHILDREN', 'NAME_FAMILY_STATUS', 'NAME_EDUCATION_TYPE', 'NAME_HOUSING_TYPE'];
    } else if (step === 2) {
      fieldsToValidate = ['AMT_INCOME_TOTAL', 'AMT_CREDIT', 'NAME_INCOME_TYPE', 'employment_years', 'NAME_CONTRACT_TYPE'];
    }
    const valid = await trigger(fieldsToValidate);
    if (valid) setStep((s) => Math.min(s + 1, 3));
  };

  const prevStep = () => setStep((s) => Math.max(s - 1, 1));

  const handleFormSubmit = (data: FormValues) => {
    // Map friendly inputs to exact Home Credit features
    const daysBirth = -Math.round(data.age_years * 365.25);
    const daysEmployed = data.employment_years < 0 ? 365243 : -Math.round(data.employment_years * 365.25);

    const payload: LoanApplicationInput = {
      CODE_GENDER: data.CODE_GENDER,
      FLAG_OWN_CAR: data.FLAG_OWN_CAR,
      FLAG_OWN_REALTY: data.FLAG_OWN_REALTY,
      CNT_CHILDREN: data.CNT_CHILDREN,
      AMT_INCOME_TOTAL: data.AMT_INCOME_TOTAL,
      AMT_CREDIT: data.AMT_CREDIT,
      AMT_ANNUITY: data.AMT_ANNUITY || undefined,
      AMT_GOODS_PRICE: data.AMT_CREDIT,
      NAME_INCOME_TYPE: data.NAME_INCOME_TYPE,
      NAME_EDUCATION_TYPE: data.NAME_EDUCATION_TYPE,
      NAME_FAMILY_STATUS: data.NAME_FAMILY_STATUS,
      NAME_HOUSING_TYPE: data.NAME_HOUSING_TYPE,
      DAYS_BIRTH: daysBirth,
      DAYS_EMPLOYED: daysEmployed,
      DAYS_REGISTRATION: -4000,
      DAYS_ID_PUBLISH: -2500,
      NAME_CONTRACT_TYPE: data.NAME_CONTRACT_TYPE,
      EXT_SOURCE_1: data.EXT_SOURCE_1,
      EXT_SOURCE_2: data.EXT_SOURCE_2,
      EXT_SOURCE_3: data.EXT_SOURCE_3,
      ORGANIZATION_TYPE: data.ORGANIZATION_TYPE,
      OCCUPATION_TYPE: data.OCCUPATION_TYPE,
      OWN_CAR_AGE: data.OWN_CAR_AGE,
      CNT_FAM_MEMBERS: data.CNT_FAM_MEMBERS,
    };

    onSubmit(payload);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 md:p-8">
      {/* Progress Steps */}
      <div className="flex items-center justify-between mb-8 pb-4 border-b border-gray-100">
        {[
          { num: 1, label: 'Applicant Profile' },
          { num: 2, label: 'Financial & Loan' },
          { num: 3, label: 'Bureau & Assets' },
        ].map((s) => (
          <div key={s.num} className="flex items-center gap-3">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
                step === s.num
                  ? 'bg-blue-600 text-white shadow-sm ring-4 ring-blue-50'
                  : step > s.num
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-100 text-gray-500'
              }`}
            >
              {step > s.num ? <CheckCircle2 className="w-5 h-5" /> : s.num}
            </div>
            <span
              className={`text-sm hidden sm:inline font-medium ${
                step === s.num ? 'text-gray-900 font-semibold' : 'text-gray-500'
              }`}
            >
              {s.label}
            </span>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit(handleFormSubmit)}>
        {/* Step 1: Personal Profile */}
        {step === 1 && (
          <div className="space-y-5 animate-fadeIn">
            <h3 className="text-lg font-semibold text-gray-900">Applicant Personal Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
                <select
                  {...register('CODE_GENDER')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                  <option value="XNA">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Age (Years)</label>
                <input
                  type="number"
                  {...register('age_years')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                {errors.age_years && (
                  <p className="text-red-500 text-xs mt-1">{errors.age_years.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Education Level</label>
                <select
                  {...register('NAME_EDUCATION_TYPE')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="Higher education">Higher Education (Bachelor/Master)</option>
                  <option value="Secondary / secondary special">Secondary / Technical</option>
                  <option value="Incomplete higher">Incomplete Higher</option>
                  <option value="Lower secondary">Lower Secondary</option>
                  <option value="Academic degree">Academic Degree (PhD)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Family Status</label>
                <select
                  {...register('NAME_FAMILY_STATUS')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="Married">Married</option>
                  <option value="Single / not married">Single</option>
                  <option value="Civil marriage">Civil Marriage</option>
                  <option value="Separated">Separated</option>
                  <option value="Widow">Widow</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Number of Children</label>
                <input
                  type="number"
                  min="0"
                  max="20"
                  {...register('CNT_CHILDREN')}
                  className={`w-full rounded-lg border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none transition-colors ${
                    errors.CNT_CHILDREN ? 'border-red-500 bg-red-50' : 'border-gray-300'
                  }`}
                />
                {errors.CNT_CHILDREN && (
                  <p className="text-red-500 text-xs mt-1 font-medium">{errors.CNT_CHILDREN.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Housing Type</label>
                <select
                  {...register('NAME_HOUSING_TYPE')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="House / apartment">House / Apartment</option>
                  <option value="Rented apartment">Rented Apartment</option>
                  <option value="With parents">With Parents</option>
                  <option value="Municipal apartment">Municipal Housing</option>
                  <option value="Office apartment">Office Apartment</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Financial Details */}
        {step === 2 && (
          <div className="space-y-5 animate-fadeIn">
            <h3 className="text-lg font-semibold text-gray-900">Financial & Requested Loan Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Total Annual Income ($)</label>
                <input
                  type="number"
                  {...register('AMT_INCOME_TOTAL')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                {errors.AMT_INCOME_TOTAL && (
                  <p className="text-red-500 text-xs mt-1">{errors.AMT_INCOME_TOTAL.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Requested Loan Amount ($)</label>
                <input
                  type="number"
                  {...register('AMT_CREDIT')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                {errors.AMT_CREDIT && (
                  <p className="text-red-500 text-xs mt-1">{errors.AMT_CREDIT.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Income Type</label>
                <select
                  {...register('NAME_INCOME_TYPE')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="Working">Salaried / Working</option>
                  <option value="Commercial associate">Commercial Associate</option>
                  <option value="Pensioner">Pensioner / Retired</option>
                  <option value="State servant">Government / State Servant</option>
                  <option value="Student">Student</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Employment Length (Years, -1 if unemployed)
                </label>
                <input
                  type="number"
                  step="0.5"
                  {...register('employment_years')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Loan Contract Type</label>
                <select
                  {...register('NAME_CONTRACT_TYPE')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="Cash loans">Cash Loans</option>
                  <option value="Revolving loans">Revolving Loans</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Expected Monthly Annuity ($)</label>
                <input
                  type="number"
                  {...register('AMT_ANNUITY')}
                  placeholder="e.g. 25000"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Credit Scores & Property */}
        {step === 3 && (
          <div className="space-y-5 animate-fadeIn">
            <h3 className="text-lg font-semibold text-gray-900">External Bureau Scores & Assets</h3>
            <p className="text-xs text-gray-500">
              Normalized external bureau credit scores (0.00 – 1.00 scale). Values around 0.5 – 0.7 represent average to strong credit history.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Bureau Score 1</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  {...register('EXT_SOURCE_1')}
                  placeholder="0.00 - 1.00"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Bureau Score 2</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  {...register('EXT_SOURCE_2')}
                  placeholder="0.00 - 1.00"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Bureau Score 3</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  {...register('EXT_SOURCE_3')}
                  placeholder="0.00 - 1.00"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Owns Real Estate / Realty?</label>
                <select
                  {...register('FLAG_OWN_REALTY')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="Y">Yes</option>
                  <option value="N">No</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Owns Vehicle / Car?</label>
                <select
                  {...register('FLAG_OWN_CAR')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="N">No</option>
                  <option value="Y">Yes</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between mt-8 pt-5 border-t border-gray-100">
          {step > 1 ? (
            <Button type="button" variant="secondary" onClick={prevStep}>
              <ArrowLeft className="w-4 h-4 mr-2" /> Back
            </Button>
          ) : (
            <div />
          )}

          {step < 3 ? (
            <Button type="button" variant="primary" onClick={nextStep}>
              Continue <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          ) : (
            <Button type="submit" variant="primary" isLoading={isLoading}>
              Run AI Risk Evaluation
            </Button>
          )}
        </div>
      </form>
    </div>
  );
}
