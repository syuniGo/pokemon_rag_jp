import React from 'react';

// Constants for better maintainability
const STAT_LABELS = {
    hp: 'HP',
    attack: '攻撃力',
    defense: '防御力',
    specialAttack: '特殊攻撃',
    specialDefense: '特殊防御',
    speed: 'スピード'
};

const MAX_STAT_VALUE = 255;

// Separate component for stats bar
const StatBar = ({ label, value }) => (
    <div className="space-y-1">
        <div className="flex justify-between text-sm">
            <span className="text-gray-300">{label}</span>
            <span className="text-white">{value}</span>
        </div>
        <div className="h-2 bg-[#1a1f36] rounded-full">
            <div
                className="h-full rounded-full bg-[#4c4dff]"
                style={{ width: `${Math.min((value / MAX_STAT_VALUE) * 100, 100)}%` }}
            />
        </div>
    </div>
);

// Separate component for tag-like items
const Tag = ({ children }) => (
    <span className="px-3 py-1 bg-[#3a3f55] text-white rounded-full text-sm">
        {children}
    </span>
);

// Separate component for section headers
const SectionHeader = ({ children }) => (
    <h3 className="text-lg font-semibold mb-2">{children}</h3>
);

// Separate component for divider
const Divider = () => (
    <div className="h-px bg-[#3a3f55] my-4" />
);

const PokemonDetailsCard = ({ pokemon }) => {
    const renderHeader = () => (
        <div className="mb-6 space-y-2">
            <div className="flex items-center justify-between">
                <div className="space-y-1">
                    <h2 className="text-2xl font-bold">{pokemon.name?.cn}</h2>
                    <div className="flex gap-2 text-sm text-gray-400">
                        <span>{pokemon.name?.en}</span>
                        <span>•</span>
                        <span>{pokemon.name?.ja}</span>
                    </div>
                </div>
                <div className="text-right">
                    <span className="text-lg font-semibold">
                        #{String(pokemon.id).padStart(3, '0')}
                    </span>
                </div>
            </div>
        </div>
    );

    const renderTypesAndAbilities = () => (
        <div className="grid grid-cols-2 mb-6">
            <div>
                <SectionHeader>タイプ</SectionHeader>
                <div className="flex gap-2">
                    {pokemon.types?.map((type, index) => (
                        <Tag key={index}>{type}</Tag>
                    ))}
                </div>
            </div>
            <div>
                <SectionHeader>特性</SectionHeader>
                <div className="flex flex-wrap gap-2">
                    {pokemon.abilities?.map((ability, index) => (
                        <Tag key={index}>{ability}</Tag>
                    ))}
                </div>
            </div>
        </div>
    );

    const renderStats = () => (
        <div className="space-y-4 w-64" style={{ width: '80%' }}>
            <SectionHeader>ステータス</SectionHeader>
            <div className="grid gap-3">
                {Object.entries(pokemon.stats || {}).map(([key, value]) => (
                    <StatBar
                        key={key}
                        label={STAT_LABELS[key]}
                        value={value}
                    />
                ))}
            </div>
        </div>
    );

    const renderAdditionalInfo = () => (
        <div className="space-y-4">
            {pokemon.relevanceAnalysis && (
                <div>
                    <SectionHeader>関連性分析</SectionHeader>
                    <p className="text-gray-300">{pokemon.relevanceAnalysis}</p>
                </div>
            )}
            {pokemon.relevanceScore && (
                <div>
                    <SectionHeader>関連性スコア</SectionHeader>
                    <p className="text-gray-300">{pokemon.relevanceScore}</p>
                </div>
            )}
            {pokemon.backgroundStory && (
                <div>
                    <SectionHeader>バックストーリー</SectionHeader>
                    <p className="text-gray-300">{pokemon.backgroundStory}</p>
                </div>
            )}
        </div>
    );

    const renderDescription = () => (
        <div>
            <SectionHeader>説明</SectionHeader>
            <p className="text-gray-300 leading-relaxed">{pokemon.description}</p>
        </div>
    );

    return (
        <div className="rounded-lg border bg-[#2a2f45] text-white border-[#3a3f55] shadow-sm">
            <div className="p-6">
                {renderHeader()}
                <Divider />
                {renderTypesAndAbilities()}
                <div className="grid grid-cols-2 gap-8">
                    {renderStats()}
                    {renderAdditionalInfo()}
                </div>
                <Divider />
                {renderDescription()}
            </div>
        </div>
    );
};

export default PokemonDetailsCard;