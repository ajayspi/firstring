'use client';

import React, { useState, useEffect } from 'react';
import { ChevronRight, Phone, Zap, Globe, Lock, Clock, ArrowRight } from 'lucide-react';
import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion';

const Website = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { scrollY } = useScroll();
  const headerOpacity = useTransform(scrollY, [0, 100], [0, 1]);
  const logoScale = useTransform(scrollY, [0, 50], [1, 0.8]);

  const agentDemos = [
    {
      name: 'Appointment Booking',
      description: 'Answers after-hours calls, books into your calendar',
      languages: ['English', 'Hindi'],
      phone: '+91 22 6953 9260',
      icon: '📅',
    },
    {
      name: 'Customer Support',
      description: '24/7 inbound support for FAQs and triage',
      languages: ['English', 'Hindi', 'Tamil'],
      phone: '+91 22 6953 9261',
      icon: '💬',
    },
    {
      name: 'Feedback Collection',
      description: 'Automated surveys and customer feedback',
      languages: ['English', 'Hindi'],
      phone: '+91 22 6953 9262',
      icon: '⭐',
    },
  ];

  const features = [
    {
      icon: <Phone className="w-6 h-6" />,
      title: 'Multilingual India-First',
      description: '10+ Indian languages including Hinglish, Tamil, Telugu, Marathi',
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: 'Sub-300ms Latency',
      description: 'Human-like response times with natural interruption handling',
    },
    {
      icon: <Globe className="w-6 h-6" />,
      title: 'Calendar Integration',
      description: 'Direct Google Calendar booking without manual data entry',
    },
    {
      icon: <Lock className="w-6 h-6" />,
      title: 'Enterprise Security',
      description: 'India-specific data residency, SOC 2 compliance, encrypted',
    },
    {
      icon: <Clock className="w-6 h-6" />,
      title: 'Deploy in Minutes',
      description: 'Go from setup to live calls in under 10 minutes',
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: 'WhatsApp Notifications',
      description: 'Owner gets instant WhatsApp alerts for every call',
    },
  ];

  const pricingPlans = [
    {
      name: 'Starter',
      price: '₹500',
      period: '/month',
      description: 'Perfect for clinics and salons',
      features: [
        '50 calls/month included',
        'Google Calendar sync',
        'WhatsApp notifications',
        'Call history & profiles',
        'Basic support',
      ],
      cta: 'Start Free Trial',
      highlighted: false,
    },
    {
      name: 'Professional',
      price: '₹1,499',
      period: '/month',
      description: 'For growing businesses',
      features: [
        'Unlimited calls',
        'Multiple calendar integrations',
        'Advanced analytics',
        'Custom workflows',
        'Priority support',
        'Multi-location support',
      ],
      cta: 'Get Started',
      highlighted: true,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: 'pricing',
      description: 'For organizations at scale',
      features: [
        'Dedicated infrastructure',
        'Custom SLA',
        'White-label solution',
        'Advanced security',
        'On-premise deployment',
        '24/7 support',
      ],
      cta: 'Contact Sales',
      highlighted: false,
    },
  ];

  const useCases = [
    {
      title: 'Dental Clinics',
      subtitle: 'Never miss an appointment',
      description: 'Answer after-hours calls, book directly into calendar, reduce no-shows by 40%',
      color: 'from-blue-500',
    },
    {
      title: 'Beauty Salons',
      subtitle: 'Boost walk-in rates',
      description: 'Handle overflow calls while staff are busy, send WhatsApp reminders',
      color: 'from-purple-500',
    },
    {
      title: 'Hotels & Restaurants',
      subtitle: 'Reservations 24/7',
      description: 'Book tables after hours, handle special requests, send confirmations',
      color: 'from-pink-500',
    },
    {
      title: 'Medical Labs',
      subtitle: 'Reduce call volume',
      description: 'Answer routine calls about reports, test schedules, directions',
      color: 'from-cyan-500',
    },
  ];

  return (
    <div className="bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white min-h-screen overflow-hidden">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
          className="absolute -top-40 -right-40 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl"
        />
        <motion.div
          animate={{ rotate: -360 }}
          transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}
          className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl"
        />
      </div>

      {/* Header */}
      <motion.header
        style={{ opacity: headerOpacity }}
        className="fixed top-0 left-0 right-0 z-50 bg-slate-950/80 backdrop-blur-md border-b border-slate-800"
      >
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <motion.div style={{ scale: logoScale }} className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
            firstring
          </motion.div>
          <nav className="hidden md:flex gap-8 text-sm">
            {['Features', 'Pricing', 'Use Cases', 'Docs'].map((item) => (
              <a key={item} href={`#${item.toLowerCase()}`} className="hover:text-cyan-400 transition">
                {item}
              </a>
            ))}
          </nav>
          <button className="bg-cyan-500 hover:bg-cyan-600 px-6 py-2 rounded-lg transition font-semibold">
            Book Demo
          </button>
        </div>
      </motion.header>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center space-y-8"
        >
          <div className="space-y-4">
            <motion.h1
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.1 }}
              className="text-6xl md:text-7xl font-black bg-gradient-to-r from-white via-cyan-200 to-cyan-400 bg-clip-text text-transparent leading-tight"
            >
              AI Receptionist for India
            </motion.h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed"
            >
              Answer after-hours calls in Hindi, English, and 8+ Indian languages. Book appointments directly into Google Calendar. WhatsApp-notify your team instantly.
            </motion.p>
          </div>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="flex gap-4 justify-center flex-wrap"
          >
            <button className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 px-8 py-4 rounded-lg font-bold text-lg flex items-center gap-2 transition transform hover:scale-105">
              Start Free Trial <ArrowRight className="w-5 h-5" />
            </button>
            <button className="border border-cyan-500 text-cyan-400 hover:bg-cyan-500/10 px-8 py-4 rounded-lg font-bold text-lg transition">
              Call Demo: +91 22 6953 9260
            </button>
          </motion.div>

          {/* Animated voice waveform */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="flex justify-center gap-1 h-16 items-center pt-8"
          >
            {[...Array(40)].map((_, i) => (
              <motion.div
                key={i}
                animate={{ height: [Math.random() * 40 + 10, Math.random() * 60 + 20, Math.random() * 40 + 10] }}
                transition={{
                  duration: 0.5 + Math.random() * 0.5,
                  repeat: Infinity,
                  delay: i * 0.02,
                }}
                className="w-1 bg-gradient-to-t from-cyan-500 to-blue-500 rounded-full"
              />
            ))}
          </motion.div>
        </motion.div>
      </section>

      {/* Social Proof */}
      <section className="py-12 px-6 border-y border-slate-800">
        <div className="max-w-7xl mx-auto">
          <p className="text-center text-slate-400 text-sm mb-8">TRUSTED BY 500+ BUSINESSES IN INDIA</p>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-8 items-center justify-items-center">
            {['Apollo Hospitals', 'Beauty Plus', 'City Hotel', 'Dr Clinic', 'Wellness Spa'].map((name) => (
              <motion.div
                key={name}
                whileHover={{ scale: 1.05 }}
                className="text-slate-500 font-semibold hover:text-cyan-400 transition"
              >
                {name}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Agent Demos */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-5xl font-black mb-4">Try Our Agents Live</h2>
            <p className="text-xl text-slate-300">Call any number below to experience AI-powered conversations</p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6">
            {agentDemos.map((agent, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: idx * 0.1 }}
                whileHover={{ y: -5 }}
                className="bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 hover:border-cyan-500 rounded-2xl p-8 transition cursor-pointer group"
              >
                <div className="text-5xl mb-4">{agent.icon}</div>
                <h3 className="text-2xl font-bold mb-2">{agent.name}</h3>
                <p className="text-slate-400 mb-6">{agent.description}</p>
                <div className="space-y-4">
                  <div className="flex gap-2 flex-wrap">
                    {agent.languages.map((lang) => (
                      <span key={lang} className="bg-cyan-500/20 text-cyan-300 px-3 py-1 rounded-full text-sm">
                        {lang}
                      </span>
                    ))}
                  </div>
                  <a
                    href={`tel:${agent.phone}`}
                    className="inline-flex items-center gap-2 bg-cyan-500/20 hover:bg-cyan-500/40 text-cyan-300 px-4 py-2 rounded-lg transition group-hover:text-cyan-200"
                  >
                    <Phone className="w-4 h-4" />
                    {agent.phone}
                  </a>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-20 px-6 bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-5xl font-black mb-4">Built for India, Built for You</h2>
            <p className="text-xl text-slate-300">Everything you need to handle every call perfectly</p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: idx * 0.05 }}
                className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700 rounded-xl p-8 hover:border-cyan-500 transition group"
              >
                <div className="text-cyan-400 mb-4 group-hover:scale-110 transition transform">{feature.icon}</div>
                <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-slate-400">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section id="usecases" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-5xl font-black mb-4">Perfect For Your Industry</h2>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6">
            {useCases.map((useCase, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: idx % 2 === 0 ? -20 : 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: idx * 0.1 }}
                className={`bg-gradient-to-br ${useCase.color}/20 border border-slate-700 rounded-2xl p-10 hover:border-cyan-400 transition`}
              >
                <h3 className="text-3xl font-bold mb-2">{useCase.title}</h3>
                <p className="text-lg text-cyan-400 mb-3">{useCase.subtitle}</p>
                <p className="text-slate-300">{useCase.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20 px-6 bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-5xl font-black mb-4">Simple, Transparent Pricing</h2>
            <p className="text-xl text-slate-300">Start free, scale as you grow</p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {pricingPlans.map((plan, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: idx * 0.1 }}
                className={`relative rounded-2xl p-10 transition transform hover:scale-105 ${
                  plan.highlighted
                    ? 'bg-gradient-to-br from-cyan-600 to-blue-600 border-2 border-cyan-400 shadow-2xl shadow-cyan-500/50'
                    : 'bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 hover:border-cyan-500'
                }`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-cyan-500 px-4 py-1 rounded-full text-sm font-bold">
                    Most Popular
                  </div>
                )}
                <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                <p className={`text-sm mb-6 ${plan.highlighted ? 'text-cyan-100' : 'text-slate-400'}`}>{plan.description}</p>
                <div className="mb-8">
                  <span className="text-5xl font-black">{plan.price}</span>
                  <span className={plan.highlighted ? 'text-cyan-100' : 'text-slate-400'}> {plan.period}</span>
                </div>
                <button
                  className={`w-full py-3 rounded-lg font-bold mb-8 transition ${
                    plan.highlighted
                      ? 'bg-white text-cyan-600 hover:bg-slate-100'
                      : 'bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/40'
                  }`}
                >
                  {plan.cta}
                </button>
                <ul className="space-y-4">
                  {plan.features.map((feature, fidx) => (
                    <li key={fidx} className="flex gap-3 items-start">
                      <ChevronRight className={`w-5 h-5 mt-0.5 flex-shrink-0 ${plan.highlighted ? 'text-white' : 'text-cyan-400'}`} />
                      <span className={plan.highlighted ? 'text-white' : 'text-slate-300'}>{feature}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          className="max-w-4xl mx-auto bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/50 rounded-3xl p-16 text-center space-y-8"
        >
          <h2 className="text-5xl font-black">Ready to Stop Missing Calls?</h2>
          <p className="text-xl text-slate-300">Join 500+ Indian businesses handling every call perfectly, 24/7</p>
          <div className="flex gap-4 justify-center flex-wrap">
            <button className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 px-10 py-4 rounded-lg font-bold text-lg transition transform hover:scale-105">
              Start Your Free Trial
            </button>
            <button className="border border-cyan-500 text-cyan-400 hover:bg-cyan-500/10 px-10 py-4 rounded-lg font-bold text-lg transition">
              Schedule a Demo
            </button>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-12 px-6 bg-slate-950/50">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-12 mb-12">
            <div>
              <h3 className="text-lg font-bold mb-4">firstring</h3>
              <p className="text-slate-400 text-sm">AI receptionist built for Indian SMBs</p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><a href="#" className="hover:text-cyan-400 transition">Features</a></li>
                <li><a href="#" className="hover:text-cyan-400 transition">Pricing</a></li>
                <li><a href="#" className="hover:text-cyan-400 transition">Use Cases</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><a href="#" className="hover:text-cyan-400 transition">About</a></li>
                <li><a href="#" className="hover:text-cyan-400 transition">Blog</a></li>
                <li><a href="#" className="hover:text-cyan-400 transition">Careers</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><a href="#" className="hover:text-cyan-400 transition">Privacy</a></li>
                <li><a href="#" className="hover:text-cyan-400 transition">Terms</a></li>
                <li><a href="#" className="hover:text-cyan-400 transition">Contact</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-800 pt-8 text-center text-slate-500 text-sm">
            <p>&copy; 2026 firstring. All rights reserved. | Made with ❤️ for India</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Website;
