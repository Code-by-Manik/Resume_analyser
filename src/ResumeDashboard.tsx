// src/ResumeDashboard.tsx
import React, { useState } from 'react';

interface Project {
  title: string;
  description: string;
  technologies: string[];
}

interface Experience {
  role: string;
  company: string;
  duration?: string;
  highlights: string[];
}

interface StructuredProfile {
  skills: string[];
  experiences: Experience[];
  projects: Project[];
}

interface AnalysisData {
  company: string;
  job_role: string;
  profile: StructuredProfile;
  fit_score: number;
  matched_keywords: string[];
  missing_keywords: string[];
  suggestions: string[];
  likely_questions: string[];
}

export const ResumeDashboard: React.FC = () => {
  const [company, setCompany] = useState<string>('');
  const [jobRole, setJobRole] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [data, setData] = useState<AnalysisData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !company.trim() || !jobRole.trim()) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('company', company);
    formData.append('job_role', jobRole);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/resume/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errJson = await response.json();
        throw new Error(errJson.detail || 'Failed to process resume');
      }

      const result: AnalysisData = await response.json();
      setData(result);
    } catch (err: any) {
      setError(err.message || 'An error occurred during file upload');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8 font-sans">
      <header className="border-b pb-4">
        <h1 className="text-3xl font-bold text-gray-900">Resume & Role Fit Analysis</h1>
        <p className="text-gray-600">Provide your target company, role, and resume PDF to evaluate role alignment and generate custom questions[cite: 1].</p>
      </header>

      {/* Target Role Form */}
      <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <form onSubmit={handleUpload} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Target Company</label>
              <input
                type="text"
                placeholder="e.g. Google, Microsoft, OpenAI"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                required
                className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Target Job Role</label>
              <input
                type="text"
                placeholder="e.g. Backend Engineer, Full Stack Developer"
                value={jobRole}
                onChange={(e) => setJobRole(e.target.value)}
                required
                className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Resume PDF</label>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              required
              className="file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer w-full"
            />
          </div>

          <button
            type="submit"
            disabled={!file || !company.trim() || !jobRole.trim() || loading}
            className="w-full py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {loading ? 'Evaluating Fit...' : 'Analyze Role Fit'}
          </button>
        </form>
        {error && <p className="mt-3 text-red-600 text-sm">{error}</p>}
      </section>

      {/* Analysis Results Display */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Verdict & Score Panel */}
          <div className="space-y-6 md:col-span-1">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 text-center">
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
                Fit Verdict for {data.company}
              </h2>
              <p className="text-lg font-bold text-gray-800 mt-1">{data.job_role}</p>

              <div className="text-5xl font-extrabold text-blue-600 my-4">{data.fit_score}%</div>
              
              <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
                data.fit_score >= 75 ? 'bg-green-100 text-green-800' :
                data.fit_score >= 50 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
              }`}>
                {data.fit_score >= 75 ? 'Strong Match' : data.fit_score >= 50 ? 'Moderate Fit' : 'Requires Optimization'}
              </span>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Matched Keywords</h3>
                <div className="flex flex-wrap gap-2">
                  {data.matched_keywords.map((kw, i) => (
                    <span key={i} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded font-medium">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Missing Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {data.missing_keywords.map((kw, i) => (
                    <span key={i} className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded font-medium">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Targeted Questions & Action Plan */}
          <div className="space-y-6 md:col-span-2">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h2 className="text-xl font-bold text-gray-800 mb-4">
                Likely Questions at {data.company}
              </h2>
              <ul className="space-y-3">
                {data.likely_questions.map((q, idx) => (
                  <li key={idx} className="p-3 bg-gray-50 rounded border-l-4 border-blue-500 text-gray-700 text-sm">
                    {q}
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h2 className="text-xl font-bold text-gray-800 mb-4">Tailored Suggestions</h2>
              <ul className="list-disc list-inside space-y-2 text-gray-600 text-sm">
                {data.suggestions.map((s, idx) => (
                  <li key={idx}>{s}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};