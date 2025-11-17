FROM node:18-alpine

WORKDIR /app

# Copiar package.json primero para aprovechar el caché de Docker
COPY package*.json ./

# Instalar dependencias
RUN npm install

COPY . .

EXPOSE 3000

# Comando de desarrollo
CMD ["npm", "start"]