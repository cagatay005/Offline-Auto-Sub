#include <iostream>
#include <string>
#include <cstdlib>

extern "C" {
    __declspec(dllexport) int altyaziyi_gom(const char* video_yolu, const char* srt_yolu, const char* cikti_yolu) { //DLL dışa aktarma
        std::string guvenli_srt_yolu = srt_yolu;    // Windows dosya yollarındaki ters eğik çizgileri FFmpeg hata vermesin diye düzelttik
        for (char& c : guvenli_srt_yolu) {
            if (c == '\\') {
                c = '/';
            }
        }
        std::cout << "Altyazi videoya gomuluyor...\n";
        // FFmpeg komutunu hazırladık -c:a copy ile sesi baştan işlemek yerine direkt kopyalayarak işlemi hızlandırdık
        std::string komut = "ffmpeg -y -i \"" + std::string(video_yolu) + 
                            "\" -vf \"subtitles='" + guvenli_srt_yolu + "'\" -c:a copy \"" + 
                            std::string(cikti_yolu) + "\"";
    
        int sonuc = std::system(komut.c_str()); // Hazırlanan komutu terminalde çalıştırdık
        
        if (sonuc == 0) {
            std::cout << "Video basariyla olusturuldu!\n";
        } else {
            std::cerr << " Hata! FFmpeg cikis kodu: " << sonuc << "\n";
        }
        return sonuc;
    }
}