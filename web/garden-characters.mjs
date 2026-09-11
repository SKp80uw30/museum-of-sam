// Visual shorthand from the supplied reference titles. Photos are never loaded.
export const birthdayName = filename => filename.replace(/\.[^.]+$/, '').replaceAll('_', ' ')
export const birthdayGreeting = filename => `${birthdayName(filename)} says Happy Birthday Sammy`
export const CHARACTERS = [
 {file:'Jay.JPG',x:-11,z:3,hair:'#967044',style:'spiky',shirt:'#62bbe5',beard:true,topGlasses:true},
 {file:'Grandpa.jpg',x:-16.8,z:-1,hair:'#eeece1',style:'balding',shirt:'#253e50',moustache:true,bow:true},
 {file:'Kylie.png',x:16,z:2,hair:'#423229',style:'shoulder',shirt:'#21506a',glasses:true,flower:'#be7edb'},
 {file:'Charlotte.png',x:-14,z:0,hair:'#664c34',style:'braided',shirt:'#8adecd'},
 {file:'Nay.JPG',x:19,z:8,hair:'#302820',style:'long',shirt:'#a265d6',crown:true},
 {file:'Timbro.JPG',x:13,z:3,hair:'#886644',style:'buzz',shirt:'#b656bd',sunglasses:'#9f62d6',lei:true},
 {file:'Thea.png',x:10,z:7,hair:'#b38a4a',style:'curly',shirt:'#28465d',scale:1},
 {file:'Elliot.JPG',x:-10,z:-2,hair:'#302d29',style:'short',shirt:'#203c50',stripe:'#d9ebeb'},
 {file:'Aimee.JPG',x:14,z:10,hair:'#b89f72',style:'long',shirt:'#284152',hood:true,pants:'#67d4d0'},
 {file:'Grandma.png',x:-17.9,z:3,hair:'#f3e9c9',style:'pixie',shirt:'#4e448c',necklace:true},
 {file:'steve.png',x:12,z:7,hair:'#997343',style:'spiky',shirt:'#244453'},
 {file:'Kat.JPG',x:-17,z:9,hair:'#b28a54',style:'long',shirt:'#334c67',flower:'#ff67ae',lei:true},
 {file:'El.JPG',x:-13,z:7,hair:'#a58159',style:'buzz',shirt:'#50c6c3',lei:true},
 {file:'Sam_aka_I_Love_Me.PNG',x:9,z:2,hair:'#a28d70',style:'shoulder',shirt:'#087e96',highlights:true},
 {file:'English_Steve.png',x:18,z:-1,hair:'#837968',style:'short',shirt:'#2b4352',hat:true,sunglasses:'#703e2f'},
 {file:'Chaz.JPG',x:-18,z:5.8,hair:'#2d2524',style:'shoulder',shirt:'#e8f7ef',freckles:true},
]
export const HONEY_FILE='Honey_with_tutu.png'
