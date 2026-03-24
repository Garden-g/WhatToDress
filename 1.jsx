import React, { useState, useEffect } from 'react';
import { 
  Shirt, 
  History, 
  Sparkles, 
  Plus, 
  CloudSun, 
  MapPin, 
  Thermometer, 
  Wind,
  CheckCircle2,
  Image as ImageIcon,
  Loader2,
  Trash2
} from 'lucide-react';

// --- 模拟数据 ---
const INITIAL_WARDROBE = [
  { id: 1, type: 'top', category: 'T恤', color: '白色', style: '休闲', season: '夏季/内搭', img: 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&q=80' },
  { id: 2, type: 'bottom', category: '牛仔裤', color: '深蓝', style: '百搭', season: '四季', img: 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&q=80' },
  { id: 3, type: 'outerwear', category: '夹克', color: '黑色', style: '酷帅', season: '春秋', img: 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400&q=80' },
  { id: 4, type: 'shoes', category: '运动鞋', color: '白/灰', style: '运动', season: '四季', img: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80' },
  { id: 5, type: 'top', category: '衬衫', color: '浅蓝', style: '商务/休闲', season: '春秋', img: 'https://images.unsplash.com/photo-1596755094514-f87e32f85e23?w=400&q=80' },
  { id: 6, type: 'bottom', category: '西装裤', color: '深灰', style: '正式', season: '四季', img: 'https://images.unsplash.com/photo-1594938298596-15102a0a256a?w=400&q=80' },
];

const MOCK_WEATHER = {
  city: '东京',
  temp: 18,
  condition: '多云转晴',
  icon: <CloudSun className="w-8 h-8 text-blue-500" />,
  details: '未来3小时降水概率10%，微风。适合多层叠穿。'
};

const SCENARIOS = ['日常上班', '周末逛街', '浪漫约会', '运动健身', '晚宴聚会'];

export default function DressWiseApp() {
  const [activeTab, setActiveTab] = useState('recommend'); // 'wardrobe', 'recommend', 'history'
  const [wardrobe, setWardrobe] = useState(INITIAL_WARDROBE);
  const [history, setHistory] = useState([]);
  const [weather, setWeather] = useState(MOCK_WEATHER);

  // 推荐状态
  const [isGenerating, setIsGenerating] = useState(false);
  const [recommendations, setRecommendations] = useState([]);
  const [scenario, setScenario] = useState('日常上班');
  const [stylePref, setStylePref] = useState('');

  // 模拟AI视觉上传
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = () => {
    setIsUploading(true);
    // 模拟API延迟和AI识别过程
    setTimeout(() => {
      const newItem = {
        id: Date.now(),
        type: 'top',
        category: '针织衫',
        color: '米色',
        style: '温柔',
        season: '秋冬',
        img: 'https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=400&q=80'
      };
      setWardrobe([newItem, ...wardrobe]);
      setIsUploading(false);
    }, 2000);
  };

  const deleteItem = (id) => {
    setWardrobe(wardrobe.filter(item => item.id !== id));
  };

  const generateOutfits = () => {
    setIsGenerating(true);
    setRecommendations([]);
    
    // 模拟大模型思考和推荐过程
    setTimeout(() => {
      // 简单模拟从衣柜中挑选
      const tops = wardrobe.filter(w => w.type === 'top');
      const bottoms = wardrobe.filter(w => w.type === 'bottom');
      const outers = wardrobe.filter(w => w.type === 'outerwear');
      const shoes = wardrobe.filter(w => w.type === 'shoes');

      const safeGet = (arr) => arr.length > 0 ? arr[Math.floor(Math.random() * arr.length)] : null;

      const mockResults = [
        {
          id: 'opt1',
          name: '精英干练风',
          items: [safeGet(tops), safeGet(bottoms), safeGet(outers), safeGet(shoes)].filter(Boolean),
          reason: `根据今天${weather.temp}°C的天气和【${scenario}】的需求，这套搭配既得体又能适应早晚温差。深色系增加专业感，同时内搭保持透气。`,
          tips: '建议搭配一条简约的银色项链提升细节感。'
        },
        {
          id: 'opt2',
          name: '轻松松弛感',
          items: [safeGet(tops), safeGet(bottoms), safeGet(shoes)].filter(Boolean),
          reason: `考虑到你偏好【${stylePref || '舒适'}】，这套去掉了厚重的外套，更适合在室内办公或短途外出，整体色彩和谐，没有压迫感。`,
          tips: '今天风不大，这套单穿刚刚好。'
        },
        {
          id: 'opt3',
          name: '下班无缝切换',
          items: [safeGet(tops), safeGet(bottoms), safeGet(outers), safeGet(shoes)].filter(Boolean),
          reason: `这套极具层次感，白天在办公室足够规矩，下班后脱掉外套直接去喝一杯也完全不突兀。完美应对突发社交。`,
          tips: '如果怕冷可以再加一条纯色围巾。'
        }
      ];
      setRecommendations(mockResults);
      setIsGenerating(false);
    }, 2500);
  };

  const acceptOutfit = (outfit) => {
    const newHistoryEntry = {
      id: Date.now(),
      date: new Date().toLocaleString(),
      weather: `${weather.city} ${weather.temp}°C ${weather.condition}`,
      scenario: scenario,
      outfit: outfit
    };
    setHistory([newHistoryEntry, ...history]);
    setActiveTab('history');
  };

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 font-sans selection:bg-zinc-900 selection:text-white pb-20 md:pb-0">
      
      {/* 侧边栏/顶部导航 */}
      <nav className="fixed bottom-0 w-full md:top-0 md:bottom-auto md:w-64 md:h-screen bg-white border-t md:border-r border-zinc-200 z-50 flex md:flex-col justify-around md:justify-start md:px-6 md:py-8 shadow-[0_-4px_20px_-15px_rgba(0,0,0,0.1)] md:shadow-none">
        <div className="hidden md:block mb-10">
          <h1 className="text-2xl font-black tracking-tighter flex items-center gap-2">
            <span className="bg-zinc-900 text-white p-1.5 rounded-lg"><Sparkles className="w-5 h-5" /></span>
            DressWise.
          </h1>
          <p className="text-xs text-zinc-500 mt-2 font-medium">智能穿搭决策引擎</p>
        </div>

        <div className="flex md:flex-col w-full">
          <NavItem 
            icon={<Sparkles className="w-5 h-5" />} 
            label="智能穿搭" 
            isActive={activeTab === 'recommend'} 
            onClick={() => setActiveTab('recommend')} 
          />
          <NavItem 
            icon={<Shirt className="w-5 h-5" />} 
            label="我的衣柜" 
            isActive={activeTab === 'wardrobe'} 
            onClick={() => setActiveTab('wardrobe')} 
          />
          <NavItem 
            icon={<History className="w-5 h-5" />} 
            label="穿搭历史" 
            isActive={activeTab === 'history'} 
            onClick={() => setActiveTab('history')} 
          />
        </div>
      </nav>

      {/* 主内容区 */}
      <main className="md:ml-64 p-4 md:p-8 max-w-5xl mx-auto min-h-screen">
        
        {/* === 智能穿搭 TAB === */}
        {activeTab === 'recommend' && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* 天气卡片 */}
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-zinc-100 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="p-4 bg-blue-50/50 rounded-2xl">
                  {weather.icon}
                </div>
                <div>
                  <div className="flex items-center gap-2 text-zinc-500 text-sm font-medium mb-1">
                    <MapPin className="w-4 h-4" /> {weather.city}
                  </div>
                  <h2 className="text-3xl font-bold flex items-center gap-2">
                    {weather.temp}°C <span className="text-xl text-zinc-400 font-medium">/ {weather.condition}</span>
                  </h2>
                </div>
              </div>
              <div className="bg-zinc-50 px-4 py-3 rounded-2xl text-sm text-zinc-600 max-w-xs leading-relaxed border border-zinc-100">
                <Wind className="w-4 h-4 inline mr-1 mb-0.5" />
                {weather.details}
              </div>
            </div>

            {/* 控制台 */}
            <div className="bg-white rounded-3xl p-6 md:p-8 shadow-sm border border-zinc-100">
              <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-zinc-900" />
                告诉 AI 你的出行计划
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div>
                  <label className="block text-sm font-semibold text-zinc-700 mb-3">你要去干嘛？ (场景)</label>
                  <div className="flex flex-wrap gap-2">
                    {SCENARIOS.map(s => (
                      <button
                        key={s}
                        onClick={() => setScenario(s)}
                        className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                          scenario === s 
                          ? 'bg-zinc-900 text-white shadow-md scale-105' 
                          : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
                        }`}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-zinc-700 mb-3">有什么特别的要求吗？ (选填风格)</label>
                  <input 
                    type="text" 
                    placeholder="例如：想要显瘦一点、想穿深色、保暖为主..." 
                    value={stylePref}
                    onChange={(e) => setStylePref(e.target.value)}
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <button 
                onClick={generateOutfits}
                disabled={isGenerating || wardrobe.length < 3}
                className="w-full bg-zinc-900 hover:bg-zinc-800 disabled:bg-zinc-300 text-white font-bold py-4 rounded-2xl flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
              >
                {isGenerating ? (
                  <><Loader2 className="w-5 h-5 animate-spin" /> 正在翻你的衣柜并计算穿搭...</>
                ) : (
                  <><Sparkles className="w-5 h-5" /> 一键帮我穿搭</>
                )}
              </button>
              {wardrobe.length < 3 && (
                <p className="text-center text-red-500 text-sm mt-3 font-medium">哥们，你衣柜里衣服太少了，先去上传几件吧。</p>
              )}
            </div>

            {/* 推荐结果 */}
            {recommendations.length > 0 && (
              <div className="space-y-6 animate-in slide-in-from-bottom-8 duration-700">
                <h3 className="text-xl font-black mb-4 px-2">AI 为你选出 3 套方案</h3>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {recommendations.map((rec, idx) => (
                    <div key={rec.id} className="bg-white rounded-3xl p-5 shadow-sm border border-zinc-100 flex flex-col hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between mb-4">
                        <span className="bg-zinc-100 text-zinc-800 text-xs font-bold px-3 py-1 rounded-full">
                          方案 {idx + 1}
                        </span>
                        <h4 className="font-bold text-lg">{rec.name}</h4>
                      </div>
                      
                      {/* 衣服缩略图网格 */}
                      <div className="grid grid-cols-2 gap-2 mb-4">
                        {rec.items.map(item => (
                          <div key={item.id} className="aspect-square rounded-xl overflow-hidden bg-zinc-100 relative group">
                            <img src={item.img} alt={item.category} className="w-full h-full object-cover" />
                            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/60 to-transparent p-2">
                              <span className="text-white text-xs font-medium">{item.category}</span>
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="flex-1 space-y-3 mb-6">
                        <p className="text-sm text-zinc-600 leading-relaxed"><span className="font-semibold text-zinc-900">💡 为什么选这套：</span>{rec.reason}</p>
                        <p className="text-xs text-amber-600 bg-amber-50 p-2 rounded-lg font-medium"><Thermometer className="w-3 h-3 inline mr-1" />{rec.tips}</p>
                      </div>

                      <button 
                        onClick={() => acceptOutfit(rec)}
                        className="w-full py-3 rounded-xl font-bold bg-zinc-100 hover:bg-zinc-900 hover:text-white transition-colors flex justify-center items-center gap-2 group"
                      >
                        <CheckCircle2 className="w-4 h-4 group-hover:scale-110 transition-transform" /> 就穿这套出门
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* === 我的衣柜 TAB === */}
        {activeTab === 'wardrobe' && (
          <div className="animate-in fade-in duration-500">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-black">我的数字衣柜</h2>
                <p className="text-sm text-zinc-500 mt-1">目前收录了 {wardrobe.length} 件单品</p>
              </div>
              <button 
                onClick={handleUpload}
                disabled={isUploading}
                className="bg-zinc-900 text-white px-4 py-2.5 rounded-xl text-sm font-bold hover:bg-zinc-800 transition-all active:scale-95 flex items-center gap-2 shadow-md"
              >
                {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                <span className="hidden md:inline">{isUploading ? 'Gemini 识别中...' : '购入新衣'}</span>
                <span className="md:hidden">{isUploading ? '识别中...' : '添加'}</span>
              </button>
            </div>

            {/* 拟物化衣柜 UI */}
            <div className="bg-[#f4f1ea] p-4 md:p-8 rounded-[2rem] border-[8px] border-zinc-200 shadow-inner relative overflow-hidden">
              
              {/* 挂衣区 (上装/外套) */}
              <div className="mb-16 relative pt-4">
                <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-6 ml-2">挂衣区 / HANGING</h3>
                
                {/* 衣架杆 */}
                <div className="h-3.5 w-[110%] -ml-[5%] bg-gradient-to-b from-zinc-400 via-zinc-300 to-zinc-400 rounded-full shadow-[0_4px_10px_rgba(0,0,0,0.15)] absolute top-[3.75rem] left-0 z-0"></div>
                
                {/* 侧视 3D 旋转翻开交互容器 - 移除了全局 perspective 避免视差畸变 */}
                <div className="flex gap-0.5 md:gap-1 overflow-x-auto pb-8 pt-4 px-4 relative z-10 min-h-[320px] items-start [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                  {wardrobe.filter(item => item.type === 'top' || item.type === 'outerwear').map(item => (
                    <div key={item.id} className="shrink-0 w-6 md:w-8 hover:w-48 md:hover:w-64 group relative transition-[width] duration-500 ease-[cubic-bezier(0.25,1,0.5,1)] cursor-crosshair h-64 md:h-[19rem] z-10 hover:z-30">
                      
                      {/* 模拟衣架钩 - 永远挂在布局中心 */}
                      <div className="w-4 md:w-5 h-8 border-t-[3px] border-r-[3px] border-zinc-400/80 rounded-tr-full absolute -top-8 left-1/2 -translate-x-1/2 group-hover:border-zinc-500 transition-colors z-20"></div>
                      
                      {/* 居中定位层：剥离 transform 冲突，提供独立的 3D 舞台 */}
                      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 md:w-64 h-full [perspective:1200px] pointer-events-none">
                        
                        {/* 衣服本体：纯净的 3D 旋转，不受父级宽度挤压影响 */}
                        <div className="w-full h-full rounded-xl md:rounded-2xl overflow-hidden shadow-[inset_2px_0_10px_rgba(0,0,0,0.2),5px_5px_15px_rgba(0,0,0,0.1)] group-hover:shadow-[0_15px_35px_rgba(0,0,0,0.25)] bg-zinc-200 border border-zinc-300/60 group-hover:border-zinc-100 origin-center transition-transform duration-500 ease-[cubic-bezier(0.25,1,0.5,1)] [transform:rotateY(-80deg)] group-hover:[transform:rotateY(0deg)] pointer-events-auto relative">
                          
                          <img src={item.img} alt={item.category} className="w-full h-full object-cover object-center" />
                          
                          {/* 未展开时的侧面阴影模拟 */}
                          <div className="absolute inset-0 bg-gradient-to-r from-black/60 via-black/20 to-transparent group-hover:opacity-0 transition-opacity duration-500 pointer-events-none"></div>

                          {/* 展开后的信息面板 */}
                          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 flex flex-col justify-between p-3 md:p-4 pointer-events-none">
                             <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); deleteItem(item.id); }} className="self-end p-2 bg-red-500/90 text-white rounded-full hover:bg-red-600 hover:scale-110 transition-transform shadow-lg backdrop-blur-sm pointer-events-auto"><Trash2 className="w-4 h-4" /></button>
                             <div className="translate-y-4 group-hover:translate-y-0 transition-transform duration-500 ease-out whitespace-nowrap overflow-hidden">
                               <span className="inline-block px-2 py-1 bg-white text-zinc-900 text-[10px] md:text-xs font-black rounded mb-1.5 shadow-sm">{item.category}</span>
                               <p className="text-white/95 text-xs md:text-sm font-medium truncate">{item.color} · {item.style}</p>
                             </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  {wardrobe.filter(item => item.type === 'top' || item.type === 'outerwear').length === 0 && (
                     <div className="w-full text-center py-10 text-zinc-400 text-sm font-medium">没衣服穿了？去买。</div>
                  )}
                </div>
              </div>

              {/* 挂裤区 (下装) - 原叠衣区 */}
              <div className="mb-16 relative pt-4">
                <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-6 ml-2">下装区 / BOTTOMS</h3>
                
                {/* 裤架杆 */}
                <div className="h-3.5 w-[110%] -ml-[5%] bg-gradient-to-b from-zinc-400 via-zinc-300 to-zinc-400 rounded-full shadow-[0_4px_10px_rgba(0,0,0,0.15)] absolute top-[3.75rem] left-0 z-0"></div>
                
                {/* 侧视 3D 旋转翻开交互容器 */}
                <div className="flex gap-0.5 md:gap-1 overflow-x-auto pb-8 pt-4 px-4 relative z-10 min-h-[320px] items-start [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                  {wardrobe.filter(item => item.type === 'bottom').map(item => (
                    <div key={item.id} className="shrink-0 w-6 md:w-8 hover:w-48 md:hover:w-64 group relative transition-[width] duration-500 ease-[cubic-bezier(0.25,1,0.5,1)] cursor-crosshair h-64 md:h-[19rem] z-10 hover:z-30">
                      
                      {/* 模拟裤架钩 */}
                      <div className="w-4 md:w-5 h-8 border-t-[3px] border-r-[3px] border-zinc-400/80 rounded-tr-full absolute -top-8 left-1/2 -translate-x-1/2 group-hover:border-zinc-500 transition-colors z-20"></div>
                      {/* 裤架夹子装饰 */}
                      <div className="w-12 h-1.5 bg-zinc-400 absolute -top-1 left-1/2 -translate-x-1/2 rounded-full z-20 group-hover:bg-zinc-500 transition-colors shadow-sm"></div>
                      
                      {/* 居中定位层：剥离 transform 冲突，提供独立的 3D 舞台 */}
                      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 md:w-64 h-full [perspective:1200px] pointer-events-none">
                        
                        {/* 衣服本体：纯净的 3D 旋转 */}
                        <div className="w-full h-full rounded-xl md:rounded-2xl overflow-hidden shadow-[inset_2px_0_10px_rgba(0,0,0,0.2),5px_5px_15px_rgba(0,0,0,0.1)] group-hover:shadow-[0_15px_35px_rgba(0,0,0,0.25)] bg-zinc-200 border border-zinc-300/60 group-hover:border-zinc-100 origin-center transition-transform duration-500 ease-[cubic-bezier(0.25,1,0.5,1)] [transform:rotateY(-80deg)] group-hover:[transform:rotateY(0deg)] pointer-events-auto relative">
                          
                          <img src={item.img} alt={item.category} className="w-full h-full object-cover object-center" />
                          
                          {/* 未展开时的侧面阴影模拟 */}
                          <div className="absolute inset-0 bg-gradient-to-r from-black/60 via-black/20 to-transparent group-hover:opacity-0 transition-opacity duration-500 pointer-events-none"></div>

                          {/* 展开后的信息面板 */}
                          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 flex flex-col justify-between p-3 md:p-4 pointer-events-none">
                             <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); deleteItem(item.id); }} className="self-end p-2 bg-red-500/90 text-white rounded-full hover:bg-red-600 hover:scale-110 transition-transform shadow-lg backdrop-blur-sm pointer-events-auto"><Trash2 className="w-4 h-4" /></button>
                             <div className="translate-y-4 group-hover:translate-y-0 transition-transform duration-500 ease-out whitespace-nowrap overflow-hidden">
                               <span className="inline-block px-2 py-1 bg-white text-zinc-900 text-[10px] md:text-xs font-black rounded mb-1.5 shadow-sm">{item.category}</span>
                               <p className="text-white/95 text-xs md:text-sm font-medium truncate">{item.color} · {item.style}</p>
                             </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  {wardrobe.filter(item => item.type === 'bottom').length === 0 && (
                     <div className="w-full text-center py-10 text-zinc-400 text-sm font-medium">没裤子穿了？去买。</div>
                  )}
                </div>
              </div>

              {/* 鞋架区 */}
              <div className="relative">
                <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-6 ml-2">鞋架 / SHOES</h3>
                {/* 金属鞋架管 */}
                <div className="h-2 w-[110%] -ml-[5%] bg-zinc-300 shadow-inner absolute bottom-4 left-0 z-0"></div>
                <div className="h-2 w-[110%] -ml-[5%] bg-zinc-400 shadow-inner absolute bottom-8 left-0 z-0"></div>
                
                <div className="flex gap-6 md:gap-8 overflow-x-auto pb-4 px-2 snap-x [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none] relative z-10 items-end">
                  {wardrobe.filter(item => item.type === 'shoes').map(item => (
                    <div key={item.id} className="snap-center shrink-0 w-28 md:w-32 group hover:-translate-y-2 hover:scale-110 transition-all duration-300 cursor-pointer">
                      <div className="aspect-[4/3] rounded-lg overflow-hidden shadow-md group-hover:shadow-2xl bg-white relative border border-zinc-200/50">
                        <img src={item.img} alt={item.category} className="w-full h-full object-cover" />
                         <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-between p-2 backdrop-blur-[2px]">
                           <button onClick={() => deleteItem(item.id)} className="self-end p-1.5 bg-red-500 text-white rounded-full hover:bg-red-600 hover:scale-110 transition-transform"><Trash2 className="w-3 h-3" /></button>
                           <div>
                             <span className="inline-block px-1.5 py-0.5 bg-white text-zinc-900 text-[10px] font-black rounded">{item.category}</span>
                           </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </div>
        )}

        {/* === 穿搭历史 TAB === */}
        {activeTab === 'history' && (
          <div className="max-w-3xl mx-auto animate-in fade-in duration-500">
            <h2 className="text-2xl font-black mb-8 flex items-center gap-2">
              <History className="w-6 h-6" /> 穿搭时光机
            </h2>

            {history.length === 0 ? (
              <div className="text-center py-20 bg-white rounded-3xl border border-zinc-100">
                <History className="w-12 h-12 text-zinc-200 mx-auto mb-4" />
                <p className="text-zinc-500 font-medium">还没记录过穿搭呢。去让AI帮你配一套吧。</p>
              </div>
            ) : (
              <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-zinc-200 before:to-transparent">
                {history.map((entry, index) => (
                  <div key={entry.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    {/* 时间轴节点 */}
                    <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white bg-zinc-900 text-white shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-sm z-10">
                      <CheckCircle2 className="w-5 h-5" />
                    </div>
                    
                    {/* 卡片内容 */}
                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-3rem)] bg-white p-5 rounded-3xl shadow-sm border border-zinc-100 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-bold text-zinc-400">{entry.date}</span>
                        <span className="text-xs bg-zinc-100 px-2 py-1 rounded-md font-medium">{entry.scenario}</span>
                      </div>
                      <p className="text-sm text-zinc-600 mb-4 flex items-center gap-1.5 bg-zinc-50 p-2 rounded-xl">
                        <CloudSun className="w-4 h-4" /> {entry.weather}
                      </p>
                      
                      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                        {entry.outfit.items.map(item => (
                          <div key={item.id} className="w-16 h-16 shrink-0 rounded-lg overflow-hidden border border-zinc-100">
                            <img src={item.img} alt="clothing" className="w-full h-full object-cover" />
                          </div>
                        ))}
                      </div>
                      <p className="text-sm font-bold mt-2">✨ {entry.outfit.name}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

      </main>
    </div>
  );
}

// 侧边栏导航项组件
function NavItem({ icon, label, isActive, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`flex md:w-full items-center gap-3 px-4 py-3 md:py-3.5 rounded-2xl md:rounded-xl transition-all font-medium text-sm md:mb-2
        ${isActive 
          ? 'bg-zinc-900 text-white shadow-md' 
          : 'text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900'
        }`}
    >
      {icon}
      <span className="hidden md:inline">{label}</span>
    </button>
  );
}