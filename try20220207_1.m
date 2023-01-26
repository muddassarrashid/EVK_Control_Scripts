clc
close all
clear all
% addpath('/home/levitech/millen/ElectroMech/MatlabLibrary/m-functions')
% addpath('/home/levitech/millen/ElectroMech/MatlabLibrary')

loadedFiles = dir('EVK_20220207_18*.csv');
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

%%Define the capture times and data length for each time capture
RecyclingTotalTime=10;%Define the repeating times
DataIntervel=floor(size(x,2)/RecyclingTotalTime);%Define the data length of each time

% % Generate plots with matlab function bag
for RecyclingTime=1:RecyclingTotalTime
for  i = 1:DataIntervel 
    
    SeparateX(i)=x(i+(RecyclingTime-1)*DataIntervel);
    SeparateY(i)=y(i+(RecyclingTime-1)*DataIntervel);


end
    [vidPSDx,frequencyx] =  periodogram(SeparateX,rectwin(length(SeparateX)),length(SeparateX),1/(time(2)-time(1)),'psd');
    [vidPSDy,frequencyy] =  periodogram(SeparateY,rectwin(length(SeparateY)),length(SeparateY),1/(time(2)-time(1)),'psd');
    PSDx(1:length(vidPSDx),RecyclingTime)=vidPSDx;
    PSDy(1:length(vidPSDy),RecyclingTime)=vidPSDy;
    Frex(1:length(vidPSDx),RecyclingTime)=frequencyx;
    Frey(1:length(vidPSDy),RecyclingTime)=frequencyy;
end

vidPSDxAve=mean(PSDx(:,:),2);
vidPSDyAve=mean(PSDy(:,:),2);
frequencyxAve=mean(Frex(:,:),2);
frequencyyAve=mean(Frey(:,:),2);


figure(1)
    semilogy(frequencyxAve,vidPSDxAve,'r')%unit:Hz
    hold on 
    semilogy(frequencyyAve,vidPSDyAve,'b')%unit:Hz  
   
        xlabel(' Frequency, (Hz) ')
        ylabel(' Amplitude ')
        set(gca,'FontSize',14)
        title( 'x&y spectrum' )
        xlim([10 100])
    legend('x','y')


