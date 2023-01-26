
clc
close all
clear all
% addpath('/home/levitech/millen/ElectroMech/MatlabLibrary/m-functions')
% addpath('/home/levitech/millen/ElectroMech/MatlabLibrary')

loadedFiles = dir('EVK_20220207_12-*.csv');
Nfiles = size(loadedFiles,1);

% Empty Arrays
clear x y time ID
x = [];
y = [];
time = [];
ID = [];

for i = 1:Nfiles
    disp(['Loaded File ' num2str(i) ' of ' num2str(Nfiles)])
    data = csvread([loadedFiles(i).folder '/' loadedFiles(i).name]);

    x       = [x data(:,4)'];
    y       = [y data(:,5)'];   
    time    = [time data(:,3)'*1e-6];    
    ID      = [ID data(:,8)'];
    
end
% M = mode(A) returns the sample mode of A, which is the most frequently 
% occurring value in A. When there are multiple values occurring equally 
% frequently, mode returns the smallest of those values.
idMode  = mode(ID);

x       = x(ID == idMode);
y       = y(ID == idMode);
time    = time(ID == idMode);


%% Generate Plots
% No average to the raw time domain data
% create PSD
% div = 20;
% psdX = createPSD(time, x, 'psd', div);
% psdY = createPSD(time, y, 'psd', div);
% 
% clf(figure(1))
% figure(1) 
%     plot(time,x)
%     hold on
%     plot(time,y)
%     hold off
% 
% sf = 1;
% clf(figure(2))
% figure(2)
%     semilogy(smooth(psdX.f,sf),  smooth(psdX.pxx,sf),'-')
%     hold on 
%     semilogy(smooth(psdY.f,sf),  smooth(psdY.pxx,sf),'-')
%     hold off
%     legend('X','Y')
%     xlim([10 150])
% % Generate plots with matlab function bag
[PSDx,frequencyx] =  periodogram(x,rectwin(length(x)),length(x),1/(time(2)-time(1)),'psd');
[PSDy,frequencyy] =  periodogram(y,rectwin(length(y)),length(y),1/(time(2)-time(1)),'psd');

clf(figure(3))
figure(3)
% subplot(1,2,1)
    semilogy(frequencyx,PSDx)%unit:Hz
    hold on 
%     xlabel(' Frequency, (Hz) ')
%     ylabel(' Amplitude ')
%     set(gca,'FontSize',14)
%     title( 'x spectrum' )
% subplot(1,2,2)
    semilogy(frequencyy,PSDy)%unit:Hz  
    hold off
        xlabel(' Frequency, (Hz) ')
        ylabel(' Amplitude ')
        set(gca,'FontSize',14)
        title( 'y spectrum' )
        xlim([10 100])
    legend('x','y')

% X = x(10000:end-1000); X = X-mean(X);
% Y = y(10000:end-1000); Y = Y-mean(Y);
% nbins = 200;
% figure(4)
%     hfig = histogram(Y,nbins);
%     hfig.Normalization = 'probability';
%     hfig.EdgeColor = 'none';
%     hold on
%     hfig = histogram(X,nbins);
%     hfig.Normalization = 'probability';
%     hfig.EdgeColor = 'none';
%     
%     hold off



