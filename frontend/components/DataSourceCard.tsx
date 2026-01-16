'use client';

import Image from 'next/image';

interface SourceConfig {
  id: string;
  name: string;
  logo: string;
  color: string;
  count: number;
}

interface DataSourceCardProps {
  source: SourceConfig;
  isActive: boolean;
  onClick: () => void;
}

export function DataSourceCard({ source, isActive, onClick }: DataSourceCardProps) {
  return (
    <button
      onClick={onClick}
      className={`
        relative group
        flex flex-col items-center justify-center
        p-6 rounded-xl
        transition-all duration-200 ease-in-out
        ${isActive
          ? 'bg-white shadow-lg border-4 border-[#542E91] transform scale-105'
          : 'bg-white shadow hover:shadow-md border-2 border-gray-200 hover:border-[#FDDC06]'
        }
      `}
      style={{ fontFamily: 'Arial, sans-serif', minHeight: '180px' }}
    >
      {/* Active indicator bar */}
      {isActive && (
        <div
          className="absolute top-0 left-0 right-0 h-1 rounded-t-xl"
          style={{ backgroundColor: '#FDDC06' }}
        />
      )}

      {/* Logo */}
      <div className="relative w-20 h-20 mb-4">
        <Image
          src={source.logo}
          alt={`${source.name} logo`}
          fill
          className="object-contain"
          priority
        />
      </div>

      {/* Name */}
      <h3 className="text-lg font-bold text-gray-900 mb-2">
        {source.name}
      </h3>

      {/* Count badge */}
      <div
        className={`
          px-3 py-1 rounded-full text-sm font-bold
          ${isActive
            ? 'bg-[#542E91] text-white'
            : 'bg-gray-100 text-gray-700 group-hover:bg-[#FDDC06] group-hover:text-black'
          }
        `}
      >
        {source.count} {source.count === 1 ? 'item' : 'items'}
      </div>

      {/* Hover glow effect */}
      {!isActive && (
        <div className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
          <div
            className="absolute inset-0 rounded-xl blur-xl"
            style={{
              background: 'linear-gradient(135deg, #542E91 0%, #FDDC06 100%)',
              opacity: 0.1
            }}
          />
        </div>
      )}
    </button>
  );
}
