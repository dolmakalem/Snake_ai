import matplotlib.pyplot as plt
import matplotlib

# Ekranda pencere açılmasını engeller, arka planda resim oluşturmaya odaklar
matplotlib.use('Agg') 

def plot(scores, mean_scores, best_scores, wall_rates, snake_rates, timeout_rates, best_avg_score):
    fig = plt.figure(figsize=(12, 9))

    # --- GRAFİK 1: SKORLAR ---
    ax1 = plt.subplot(2, 1, 1)
    plt.title('Eğitim Süreci: Skorlar', fontsize=14, fontweight='bold')
    plt.xlabel('Oyun (Game)')
    plt.ylabel('Skor')
    
    # --- DEVASA SİLİK YAZILAR (FİLİGRAN / WATERMARK) ---
    if len(mean_scores) > 0:
        current_avg = mean_scores[-1]
        
        # BEST AVG Skoru (Arka planda, merkezin biraz üstünde)
        ax1.text(0.5, 0.65, f'BEST AVG: {best_avg_score:.2f}', 
                 transform=ax1.transAxes, 
                 fontsize=60, fontweight='bold', color='green', 
                 ha='center', va='center', alpha=0.15, zorder=0)
                 
        # Anlık AVG Skoru (Arka planda, merkezin biraz altında)
        ax1.text(0.5, 0.35, f'AVG: {current_avg:.2f}', 
                 transform=ax1.transAxes, 
                 fontsize=60, fontweight='bold', color='orange', 
                 ha='center', va='center', alpha=0.15, zorder=0)
    
    # Çizgiler (Yeşil çizgi hala anlık ulaşılan "Best Score" rekorunu göstermeye devam edecek)
    plt.plot(scores, label='Anlık Skor', color='lightblue', alpha=0.6)
    plt.plot(mean_scores, label='Ortalama Skor', color='orange', linewidth=2)
    plt.plot(best_scores, label='En İyi Skor (Best Score)', color='green', linewidth=2)
    plt.legend(loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.5)

    # --- GRAFİK 2: ÖLÜM ORANLARI ---
    plt.subplot(2, 1, 2)
    plt.title('Ölüm Sebepleri Dağılımı (%)', fontsize=14, fontweight='bold')
    plt.xlabel('Oyun (Game)')
    plt.ylabel('Oran (%)')
    
    plt.plot(wall_rates, label='Duvar (%)', color='red', linewidth=1.5)
    plt.plot(snake_rates, label='Gövde (%)', color='purple', linewidth=2)
    plt.plot(timeout_rates, label='Açlık (%)', color='gray', linewidth=1.5)
    plt.ylim(0, 105) 
    plt.legend(loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig('training_plot.png')
    plt.close(fig)