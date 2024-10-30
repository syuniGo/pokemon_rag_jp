import React, { useState, useCallback, useEffect } from 'react';
import { Input } from "/components/ui/input";
import { Button } from "/components/ui/button";
import { ChevronLeft, ChevronRight, Loader2, X } from 'lucide-react';
import "/src/tw.css";
import PokemonDetailsCard from './PokemonDetailsCard';

const DISPLAY_COUNT = 3;
const API_ENDPOINT = 'http://localhost:8080/api/search';

const STYLES = {
  container: "min-h-screen bg-[#1a1f36]",
  content: "mx-auto max-w-5xl p-6",
  header: "text-2xl font-bold text-white text-center mb-6",
  searchContainer: "relative w-full max-w-md mx-auto mb-12",
  searchInput: "w-full bg-[#2a2f45] border-[#3a3f55] text-white placeholder:text-gray-400 pr-20",
  clearButton: "absolute right-10 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white",
  searchButton: "absolute right-0 top-0 h-full bg-[#4c4dff] hover:bg-[#3a3bff]",
  navButton: "bg-[#2a2f45] hover:bg-[#3a3f55] text-white rounded-full p-2 z-20",
  cardsWrapper: "relative flex items-center justify-center gap-4",
  resultsGrid: "grid grid-cols-2 gap-4 mt-8",
  resultCard: "bg-[#2a2f45] rounded-lg p-4"
};

const NavigationButton = ({ direction, onClick }) => (
  <Button
    onClick={onClick}
    variant="ghost"
    className={STYLES.navButton}
  >
    {direction === 'left' ? 
      <ChevronLeft className="h-6 w-6" /> : 
      <ChevronRight className="h-6 w-6" />
    }
  </Button>
);

const PokemonCard = ({ pokemon, isSelected, onClick }) => {
  const cardScale = isSelected ? 'scale-125 z-10' : 'scale-100';
  
  const baseCardStyle = `bg-[#2a2f45] rounded-lg p-4 ${
    pokemon.isRelevant ? 'ring-2 ring-[#FFD700] bg-[#313866]' : ''
  } ${
    isSelected ? 'bg-[#3a3f55] shadow-xl shadow-[#4c4dff]/20' : 'hover:bg-[#3a3f55]'
  }`;

  const imageContainerStyle = `w-full aspect-square rounded-lg p-2 mb-2 ${
    pokemon.isRelevant ? 'bg-[#232655]' : 'bg-[#1a1f36]'
  }`;

  return (
    <div 
      onClick={onClick} 
      className={`transform transition-all duration-300 cursor-pointer ${cardScale}`}
    >
      <div className={baseCardStyle}>
        <div className={imageContainerStyle}>
          <img
            src={`https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${pokemon.id}.png`}
            alt={pokemon.name}
            className="w-full h-full object-contain"
          />
        </div>
        <div className="text-center p-4">
          <p className={`font-medium truncate ${
            pokemon.isRelevant ? 'text-[#FFD700]' : 'text-white'
          }`}>
            {pokemon.name}
          </p>
          <div className="mt-2 space-y-1">
            <p className="text-xs text-gray-300">
              戦闘力: {pokemon.powerRating}
            </p>
          </div>
          {pokemon.isRelevant && (
            <span className="absolute inline-block mt-1 px-2 py-0.5 bg-[#FFD700]/20 text-[#FFD700] text-xs rounded-full">
              おすすめ
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

const SearchResults = ({ searchResponse }) => (
  <div className={STYLES.resultsGrid}>
    <div className={STYLES.resultCard}>
      <h3 className="font-medium text-white mb-2">関連度</h3>
      <p className="text-gray-300">{searchResponse.relevance}</p>
    </div>
    <div className={STYLES.resultCard}>
      <h3 className="font-medium text-white mb-2">詳細説明</h3>
      <p className="text-gray-300">{searchResponse.relevance_explanation}</p>
    </div>
  </div>
);

const SearchBar = ({ search, isLoading, onSearch, onChange, onClear }) => (
  <div className={STYLES.searchContainer}>
    <div className="relative">
      <Input
        value={search}
        onChange={onChange}
        className={STYLES.searchInput}
        placeholder="ポケモンを検索..."
      />
      {search && (
        <button onClick={onClear} className={STYLES.clearButton}>
          <X className="h-4 w-4" />
        </button>
      )}
      <Button
        onClick={onSearch}
        disabled={isLoading || !search.trim()}
        className={STYLES.searchButton}
      >
        {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "検索"}
      </Button>
    </div>
  </div>
);

export default function PokemonSearch() {
  const [search, setSearch] = useState('');
  const [pokemonList, setPokemonList] = useState([]);
  const [displayList, setDisplayList] = useState([]); 
  const [searchResponse, setSearchResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);

  const updateDisplayList = useCallback((newIndex) => {
    const listLength = pokemonList.length;
    const displayItems = [];

    for (let i = 0; i < DISPLAY_COUNT; i++) {
      const index = (newIndex + i) % listLength;
      displayItems.push({
        ...pokemonList[index],
        displayIndex: i 
      });
    }

    setDisplayList(displayItems);
  }, [pokemonList]);

  useEffect(() => {
    if (pokemonList.length > 0) {
      updateDisplayList(0);
      setCurrentIndex(0);
    }
  }, [pokemonList, updateDisplayList]);

  const handleSearch = async () => {
    if (!search.trim()) return;
    setIsLoading(true);
    try {
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: search, top_k: 5 }),
      });
      const data = await response.json();
      setSearchResponse(data);
      
      if (data?.search_results && data?.pokemon_entries) {
        const mostRelevantNo = data.summary?.most_relevant_pokemon?.no;
        const newPokemonList = data.search_results.map(pokemon => ({
          id: pokemon.no,
          name: pokemon.nameCn,
          isRelevant: pokemon.no == mostRelevantNo,
          powerRating: data.pokemon_entries.find(entry => entry.no == pokemon.no)?.power_rating || 'N/A',
          relevanceScore: data.pokemon_entries.find(entry => entry.no == pokemon.no)?.relevance_score || 0,
          relevanceAnalysis: data.pokemon_entries.find(entry => entry.no == pokemon.no)?.relevance_analysis || '',
          backgroundStory: data.pokemon_entries.find(entry => entry.no == pokemon.no)?.background_story || ''
        }));
        setPokemonList(newPokemonList);
      }
    } catch (error) {
      console.error('エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNavigation = useCallback((direction) => {
    const delta = direction === 'next' ? 1 : -1;
    const newIndex = (currentIndex + delta + pokemonList.length) % pokemonList.length;
    setCurrentIndex(newIndex);
    updateDisplayList(newIndex);
  }, [currentIndex, pokemonList.length, updateDisplayList]);

  const handleClearSearch = () => {
    setSearch('');
    setPokemonList([]);
    setDisplayList([]);
    setSearchResponse(null);
  };

  const handlePokemonClick = (index) => {
    if (index === 1) return;
    
    const delta = index === 0 ? -1 : 1;
    const newIndex = (currentIndex + delta + pokemonList.length) % pokemonList.length;
    setCurrentIndex(newIndex);
    updateDisplayList(newIndex);
  };

  const getSelectedPokemonData = () => {
    if (!displayList[1] || !searchResponse?.search_results) return null;

    const selectedPokemon = displayList[1];
    const searchResult = searchResponse.search_results.find(
      pokemon => pokemon.no === selectedPokemon.id
    );

    return {
      name: {
        cn: searchResult.nameCn,
        en: searchResult.nameEn,
        ja: searchResult.nameJa
      },
      id: searchResult.no,
      stats: searchResult.stats,
      types: searchResult.types,
      abilities: searchResult.abilities,
      description: searchResult.description,
      relevanceAnalysis: selectedPokemon.relevanceAnalysis,
      backgroundStory: selectedPokemon.backgroundStory,
      relevanceScore: selectedPokemon.relevanceScore
    };
  };

  return (
    <div className={STYLES.container}>
      <div className={STYLES.content}>
        <h1 className={STYLES.header}>
          キーワードでポケモンを探そう
        </h1>

        <SearchBar
          search={search}
          isLoading={isLoading}
          onSearch={handleSearch}
          onChange={(e) => setSearch(e.target.value)}
          onClear={handleClearSearch}
        />

        {displayList.length > 0 && (
          <div className="mb-8">
            <div className={STYLES.cardsWrapper}>
              <NavigationButton
                direction="left"
                onClick={() => handleNavigation('prev')}
              />

              <div className="flex justify-center items-center gap-4">
                {displayList.map((pokemon, index) => (
                  <PokemonCard
                    key={`${pokemon.id}-${pokemon.displayIndex}`}
                    pokemon={pokemon}
                    isSelected={index === 1}
                    onClick={() => handlePokemonClick(index)}
                  />
                ))}
              </div>

              <NavigationButton
                direction="right"
                onClick={() => handleNavigation('next')}
              />
            </div>
          </div>
        )}

        {displayList.length > 0 && searchResponse?.search_results[1] && (
          <PokemonDetailsCard 
            pokemon={getSelectedPokemonData()} 
          />
        )}
        
        {searchResponse && <SearchResults searchResponse={searchResponse} />}
      </div>
    </div>
  );
}